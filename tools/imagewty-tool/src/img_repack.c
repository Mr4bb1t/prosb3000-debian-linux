/**
 * @file img_repack.c
 * @brief Safe, streaming repacking of IMAGEWTY dumps.
 */

#include "img_repack.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "checksum.h"
#include "config_file.h"
#include "img_header.h"

#define COPY_BUFFER_SIZE 0x10000

static int join_path(char* out, size_t out_size, const char* folder, const char* name)
{
    if (!is_safe_dump_name(name))
        return -1;
    int written = snprintf(out, out_size, "%s/%s", folder, name);
    return (written < 0 || (size_t)written >= out_size) ? -1 : 0;
}

static void put_uint32_le(uint8_t* destination, uint32_t value)
{
    destination[0] = (uint8_t)value;
    destination[1] = (uint8_t)(value >> 8);
    destination[2] = (uint8_t)(value >> 16);
    destination[3] = (uint8_t)(value >> 24);
}

static int copy_exact(FILE* input, FILE* output, uint64_t length)
{
    uint8_t buffer[COPY_BUFFER_SIZE];
    while (length > 0)
    {
        size_t wanted = length > sizeof(buffer) ? sizeof(buffer) : (size_t)length;
        size_t received = fread(buffer, 1, wanted, input);
        if (received != wanted || fwrite(buffer, 1, received, output) != received)
            return -1;
        length -= received;
    }
    return 0;
}

static uint64_t aligned_length(uint64_t length)
{
    return (length + PADDING_ALIGNMENT - 1) / PADDING_ALIGNMENT * PADDING_ALIGNMENT;
}

static int get_file_size(const char* path, uint64_t* size)
{
    FILE* file = fopen(path, "rb");
    if (!file)
        return -1;
    int failed = fseeko(file, 0, SEEK_END) != 0;
    off_t end = failed ? -1 : ftello(file);
    if (fclose(file) != 0)
        failed = 1;
    if (failed || end < 0)
        return -1;
    *size = (uint64_t)end;
    return 0;
}

static int preflight_sources(const char* dump_folder, const char* output_file,
                             const ImageWTYHeader* hdr, const ImageWTYFileHeader* files)
{
    char cfg_path[1024];
    struct stat cfg_stat;
    if (join_path(cfg_path, sizeof(cfg_path), dump_folder, "image.cfg") != 0 ||
        stat(cfg_path, &cfg_stat) != 0)
        return -1;

    struct stat* sources = calloc(hdr->num_files, sizeof(*sources));
    if (!sources)
        return -1;
    int failed = 0;
    struct stat output_stat;
    int output_exists = stat(output_file, &output_stat) == 0;
    for (uint32_t i = 0; i < hdr->num_files; i++)
    {
        char path[1024];
        const char* source = files[i].source_path[0] ? files[i].source_path : files[i].filename;
        uint64_t ignored;
        if (join_path(path, sizeof(path), dump_folder, source) != 0 ||
            stat(path, &sources[i]) != 0 || !S_ISREG(sources[i].st_mode) ||
            get_file_size(path, &ignored) != 0)
        {
            fprintf(stderr, "Cannot access input file '%s'.\n", source);
            failed = 1;
            break;
        }
        if (output_exists && sources[i].st_dev == output_stat.st_dev &&
            sources[i].st_ino == output_stat.st_ino)
        {
            fprintf(stderr, "Output file must not replace input '%s'.\n", source);
            failed = 1;
            break;
        }
        int writable = is_checksum_file(files[i].filename);
        if (writable && sources[i].st_dev == cfg_stat.st_dev &&
            sources[i].st_ino == cfg_stat.st_ino)
        {
            fprintf(stderr, "Checksum source '%s' must not alias image.cfg.\n", source);
            failed = 1;
            break;
        }
        for (uint32_t j = 0; j < i; j++)
        {
            if ((writable || is_checksum_file(files[j].filename)) &&
                sources[i].st_dev == sources[j].st_dev && sources[i].st_ino == sources[j].st_ino)
            {
                fprintf(stderr, "Conflicting checksum source aliases at entries %u and %u.\n",
                        j + 1, i + 1);
                failed = 1;
                break;
            }
        }
        if (failed)
            break;
    }
    free(sources);
    return failed ? -1 : 0;
}

static void fill_global_header(uint8_t* buffer, const ImageWTYHeader* hdr)
{
    memset(buffer, 0, IMG_HEADER_HEADER_SIZE);
    memcpy(buffer, hdr->magic, 8);
    put_uint32_le(buffer + 0x08, hdr->header_version);
    put_uint32_le(buffer + 0x0c, hdr->header_size);
    put_uint32_le(buffer + 0x10, hdr->base_ram);
    put_uint32_le(buffer + 0x14, hdr->format_version);
    put_uint32_le(buffer + 0x18, hdr->total_image_size);
    put_uint32_le(buffer + 0x1c, hdr->header_size_aligned);
    put_uint32_le(buffer + 0x20, hdr->file_header_length);
    put_uint32_le(buffer + 0x24, hdr->usb_product_id);
    put_uint32_le(buffer + 0x28, hdr->usb_vendor_id);
    put_uint32_le(buffer + 0x2c, hdr->hardware_id);
    put_uint32_le(buffer + 0x30, hdr->firmware_id);
    put_uint32_le(buffer + 0x34, hdr->unknown1);
    put_uint32_le(buffer + 0x38, hdr->unknown2);
    put_uint32_le(buffer + 0x3c, hdr->num_files);
    put_uint32_le(buffer + 0x40, hdr->unknown3);
}

static int write_file_headers(FILE* output, const ImageWTYHeader* hdr,
                              const ImageWTYFileHeader* files)
{
    uint8_t* buffer = calloc(1, hdr->file_header_length);
    if (!buffer)
        return -1;

    for (uint32_t i = 0; i < hdr->num_files; i++)
    {
        const ImageWTYFileHeader* fh = &files[i];
        memset(buffer, 0, hdr->file_header_length);
        put_uint32_le(buffer, fh->filename_length);
        put_uint32_le(buffer + 0x04, fh->header_size);
        memcpy(buffer + 0x08, fh->maintype, 8);
        memcpy(buffer + 0x10, fh->subtype, 16);
        put_uint32_le(buffer + 0x20, fh->unknown0);
        memcpy(buffer + 0x24, fh->filename, 256);
        put_uint32_le(buffer + 0x124, fh->stored_length);
        put_uint32_le(buffer + 0x128, fh->pad1);
        put_uint32_le(buffer + 0x12c, fh->original_length);
        put_uint32_le(buffer + 0x130, fh->pad2);
        put_uint32_le(buffer + 0x134, fh->offset);
        uint64_t position = (uint64_t)FILE_HEADERS_START + (uint64_t)i * hdr->file_header_length;
        if (fseeko(output, (off_t)position, SEEK_SET) != 0 ||
            fwrite(buffer, 1, hdr->file_header_length, output) != hdr->file_header_length)
        {
            free(buffer);
            return -1;
        }
    }
    free(buffer);
    return 0;
}

int repack_image(const char* dump_folder, const char* output_file)
{
    if (!dump_folder || !output_file)
        return 1;

    char cfg_path[1024];
    if (join_path(cfg_path, sizeof(cfg_path), dump_folder, "image.cfg") != 0)
    {
        fprintf(stderr, "Configuration path is too long.\n");
        return 1;
    }

    ImageWTYHeader hdr;
    ImageWTYFileHeader* files = NULL;
    int config_status = load_image_config(cfg_path, &hdr, &files);
    if (config_status != 0 || !files)
    {
        fprintf(stderr, "Invalid image.cfg in '%s'.\n", dump_folder);
        return 1;
    }
    struct stat cfg_stat;
    struct stat output_stat;
    if (stat(cfg_path, &cfg_stat) == 0 && stat(output_file, &output_stat) == 0 &&
        cfg_stat.st_dev == output_stat.st_dev && cfg_stat.st_ino == output_stat.st_ino)
    {
        fprintf(stderr, "Output file must not replace image.cfg.\n");
        free(files);
        return 1;
    }
    if (preflight_sources(dump_folder, output_file, &hdr, files) != 0)
    {
        free(files);
        return 1;
    }

    uint64_t offset =
        (uint64_t)FILE_HEADERS_START + (uint64_t)hdr.num_files * hdr.file_header_length;
    for (uint32_t i = 0; i < hdr.num_files; i++)
    {
        char path[1024];
        const char* source = files[i].source_path[0] ? files[i].source_path : files[i].filename;
        uint64_t size;
        if (join_path(path, sizeof(path), dump_folder, source) != 0 ||
            get_file_size(path, &size) != 0 || size > UINT32_MAX)
        {
            fprintf(stderr, "Invalid input file '%s'.\n", source);
            free(files);
            return 1;
        }
        uint64_t stored = aligned_length(size);
        if (is_checksum_file(files[i].filename) && size < 4)
        {
            fprintf(stderr, "Checksum file '%s' must contain at least four bytes.\n", source);
            free(files);
            return 1;
        }
        if (offset > UINT32_MAX || stored > UINT32_MAX || offset + stored > UINT32_MAX)
        {
            fprintf(stderr, "IMAGEWTY 32-bit size limit exceeded at '%s'.\n", source);
            free(files);
            return 1;
        }
        files[i].original_length = (uint32_t)size;
        files[i].stored_length = (uint32_t)stored;
        files[i].offset = (uint32_t)offset;
        offset += stored;
    }

    char temporary[1024];
    int written = snprintf(temporary, sizeof(temporary), "%s.tmp.%ld", output_file, (long)getpid());
    if (written < 0 || (size_t)written >= sizeof(temporary))
    {
        fprintf(stderr, "Output path is too long.\n");
        free(files);
        return 1;
    }
    FILE* output = fopen(temporary, "wbx");
    if (!output)
    {
        fprintf(stderr, "Cannot create temporary output '%s': %s\n", temporary, strerror(errno));
        free(files);
        return 1;
    }

    uint32_t* checksums = calloc(hdr.num_files, sizeof(*checksums));
    int failed = !checksums || prepare_vfile_checksums(dump_folder, &hdr, files, checksums) != 0;
    uint8_t global_header[IMG_HEADER_HEADER_SIZE];
    fill_global_header(global_header, &hdr);
    if (!failed &&
        (fwrite(global_header, 1, sizeof(global_header), output) != sizeof(global_header) ||
         write_file_headers(output, &hdr, files) != 0))
    {
        fprintf(stderr, "Error writing image headers.\n");
        failed = 1;
    }

    uint8_t padding[PADDING_ALIGNMENT] = {0};
    for (uint32_t i = 0; i < hdr.num_files && !failed; i++)
    {
        char path[1024];
        const char* source = files[i].source_path[0] ? files[i].source_path : files[i].filename;
        if (join_path(path, sizeof(path), dump_folder, source) != 0 ||
            fseeko(output, (off_t)files[i].offset, SEEK_SET) != 0)
        {
            failed = 1;
            break;
        }
        FILE* input = fopen(path, "rb");
        if (!input)
        {
            failed = 1;
            break;
        }
        uint64_t remaining = files[i].original_length;
        int copy_failed = 0;
        if (is_checksum_file(files[i].filename))
        {
            uint8_t replacement[4];
            put_uint32_le(replacement, checksums[i]);
            copy_failed =
                fseeko(input, 4, SEEK_SET) != 0 ||
                fwrite(replacement, 1, sizeof(replacement), output) != sizeof(replacement);
            remaining -= sizeof(replacement);
        }
        if (!copy_failed)
            copy_failed = copy_exact(input, output, remaining) != 0;
        int close_failed = fclose(input) != 0;
        uint32_t pad = files[i].stored_length - files[i].original_length;
        if (copy_failed || close_failed || (pad && fwrite(padding, 1, pad, output) != pad))
        {
            fprintf(stderr, "Error packing '%s'.\n", source);
            failed = 1;
            break;
        }
        printf("Packed: %s (original: %u, stored: %u)\n", source, files[i].original_length,
               files[i].stored_length);
    }

    if (fflush(output) != 0)
    {
        fprintf(stderr, "Error flushing output image.\n");
        failed = 1;
    }
    if (fclose(output) != 0)
    {
        fprintf(stderr, "Error closing output image.\n");
        failed = 1;
    }
    if (!failed && rename(temporary, output_file) != 0)
    {
        fprintf(stderr, "Cannot finalize '%s': %s\n", output_file, strerror(errno));
        failed = 1;
    }
    if (failed)
        unlink(temporary);

    free(checksums);
    free(files);
    if (failed)
        return 1;
    printf("Repack completed successfully: %s\n", output_file);
    return 0;
}
