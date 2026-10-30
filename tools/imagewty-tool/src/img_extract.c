/**
 * @file img_extract.c
 * @brief Safe, streaming extraction of IMAGEWTY images.
 */

#include "img_extract.h"

#include <errno.h>
#include <libgen.h>
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

static int copy_exact(FILE* input, FILE* output, uint64_t length)
{
    uint8_t buffer[COPY_BUFFER_SIZE];
    while (length > 0)
    {
        size_t wanted = length > sizeof(buffer) ? sizeof(buffer) : (size_t)length;
        size_t received = fread(buffer, 1, wanted, input);
        if (received != wanted)
            return -1;
        if (fwrite(buffer, 1, received, output) != received)
            return -1;
        length -= received;
    }
    return 0;
}

static void remove_staging_directory(const char* path, const ImageWTYHeader* hdr,
                                     const ImageWTYFileHeader* files)
{
    if (!path)
        return;
    if (hdr && files)
    {
        for (uint32_t i = 0; i < hdr->num_files; i++)
        {
            char filepath[1024];
            if (join_path(filepath, sizeof(filepath), path, files[i].source_path) == 0)
                unlink(filepath);
        }
    }
    char cfg_path[1024];
    if (snprintf(cfg_path, sizeof(cfg_path), "%s/image.cfg", path) > 0)
        unlink(cfg_path);
    rmdir(path);
}

static int source_path_used(const ImageWTYFileHeader* files, uint32_t count, const char* candidate)
{
    if (strcmp(candidate, "image.cfg") == 0)
        return 1;
    for (uint32_t i = 0; i < count; i++)
    {
        if (strcmp(files[i].source_path, candidate) == 0)
            return 1;
    }
    return 0;
}

static int assign_source_paths(ImageWTYFileHeader* files, uint32_t count)
{
    errno = 0;
    long filesystem_limit = pathconf(".", _PC_NAME_MAX);
    if (filesystem_limit < 0 && errno != 0)
        return -1;
    size_t name_limit =
        (filesystem_limit > 0 && filesystem_limit < 255) ? (size_t)filesystem_limit : 255;
    for (uint32_t i = 0; i < count; i++)
    {
        unsigned int occurrence = 1;
        for (;; occurrence++)
        {
            char candidate[257];
            if (occurrence == 1 && strlen(files[i].filename) <= name_limit)
            {
                if (snprintf(candidate, sizeof(candidate), "%s", files[i].filename) < 0)
                    return -1;
            }
            else
            {
                const char* dot = strrchr(files[i].filename, '.');
                char suffix[16];
                int suffix_length = snprintf(suffix, sizeof(suffix), "__%u", occurrence);
                if (suffix_length < 0 || (size_t)suffix_length >= name_limit)
                    return -1;
                size_t available = name_limit - (size_t)suffix_length;
                /* If the extension alone is too long, shorten the whole name. */
                if (dot && strlen(dot) >= available)
                    dot = NULL;
                size_t stem_length =
                    dot ? (size_t)(dot - files[i].filename) : strlen(files[i].filename);
                size_t extension_length = dot ? strlen(dot) : 0;
                if (stem_length > available - extension_length)
                    stem_length = available - extension_length;
                int written = snprintf(candidate, sizeof(candidate), "%.*s%s%s", (int)stem_length,
                                       files[i].filename, suffix, dot ? dot : "");
                if (written < 0 || (size_t)written >= sizeof(candidate))
                    return -1;
            }
            if (!source_path_used(files, i, candidate))
            {
                snprintf(files[i].source_path, sizeof(files[i].source_path), "%s", candidate);
                break;
            }
        }
    }
    return 0;
}

int extract_image(const char* img_filename)
{
    if (!img_filename)
        return 1;

    FILE* input = fopen(img_filename, "rb");
    if (!input)
    {
        fprintf(stderr, "Cannot open image '%s': %s\n", img_filename, strerror(errno));
        return 1;
    }

    ImageWTYHeader hdr;
    if (read_image_header(input, &hdr) != 0 || memcmp(hdr.magic, IMAGEWTY_MAGIC, 8) != 0)
    {
        fprintf(stderr, "Error: '%s' is not a valid IMAGEWTY image.\n", img_filename);
        fclose(input);
        return 1;
    }
    ImageWTYFileHeader* files = read_all_file_headers(input, hdr.num_files, hdr.file_header_length);
    if (!files || validate_image_layout(input, &hdr, files) != 0 ||
        assign_source_paths(files, hdr.num_files) != 0)
    {
        fprintf(stderr, "Error: invalid or unsupported image layout.\n");
        free(files);
        fclose(input);
        return 1;
    }

    char path_copy[1024];
    int copied = snprintf(path_copy, sizeof(path_copy), "%s", img_filename);
    if (copied < 0 || (size_t)copied >= sizeof(path_copy))
    {
        fprintf(stderr, "Image path is too long.\n");
        free(files);
        fclose(input);
        return 1;
    }

    char dump_dir[1024];
    int written = snprintf(dump_dir, sizeof(dump_dir), "%s.dump", basename(path_copy));
    if (written < 0 || (size_t)written >= sizeof(dump_dir))
    {
        fprintf(stderr, "Dump directory path is too long.\n");
        free(files);
        fclose(input);
        return 1;
    }
    struct stat st;
    if (lstat(dump_dir, &st) == 0 || errno != ENOENT)
    {
        fprintf(stderr, "Refusing to overwrite existing dump '%s'.\n", dump_dir);
        free(files);
        fclose(input);
        return 1;
    }

    char staging[1024];
    written = snprintf(staging, sizeof(staging), "%s.tmp.%ld", dump_dir, (long)getpid());
    if (written < 0 || (size_t)written >= sizeof(staging) || mkdir(staging, 0700) != 0)
    {
        fprintf(stderr, "Cannot create staging directory: %s\n", strerror(errno));
        free(files);
        fclose(input);
        return 1;
    }

    int failed = 0;
    for (uint32_t i = 0; i < hdr.num_files && !failed; i++)
    {
        ImageWTYFileHeader* fh = &files[i];
        char filepath[1024];
        if (join_path(filepath, sizeof(filepath), staging, fh->source_path) != 0 ||
            fseeko(input, (off_t)fh->offset, SEEK_SET) != 0)
        {
            failed = 1;
            break;
        }
        FILE* output = fopen(filepath, "wb");
        if (!output)
        {
            failed = 1;
            break;
        }
        int copy_failed = copy_exact(input, output, fh->original_length) != 0;
        int close_failed = fclose(output) != 0;
        if (copy_failed || close_failed)
        {
            fprintf(stderr, "Error extracting '%s'.\n", fh->filename);
            failed = 1;
            break;
        }
        printf("Extracting: %s (%u bytes)\n", fh->source_path, fh->original_length);
    }

    char cfg_path[1024];
    if (!failed)
    {
        int cfg_written = snprintf(cfg_path, sizeof(cfg_path), "%s/image.cfg", staging);
        if (cfg_written < 0 || (size_t)cfg_written >= sizeof(cfg_path) ||
            write_image_config(cfg_path, &hdr, files, hdr.num_files) != 0)
            failed = 1;
    }
    if (fclose(input) != 0)
        failed = 1;

    if (failed || rename(staging, dump_dir) != 0)
    {
        if (!failed)
            fprintf(stderr, "Cannot finalize dump '%s': %s\n", dump_dir, strerror(errno));
        remove_staging_directory(staging, &hdr, files);
        free(files);
        return 1;
    }

    printf("image.cfg successfully written in '%s'\n", dump_dir);
    printf("\nVerifying extracted files using V*.fex checksums...\n");
    int checksum_status = verify_vfiles_checksums(dump_dir, &hdr, files);
    free(files);
    return checksum_status == 0 ? 0 : 1;
}
