/**
 * @file checksum.c
 * @brief IMAGEWTY V-file checksum handling.
 */

#include "checksum.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define CHECKSUM_BUFFER_SIZE 0x10000

static int join_dump_path(char* out, size_t out_size, const char* folder, const char* name)
{
    if (!out || !folder || !is_safe_dump_name(name))
        return -1;
    int written = snprintf(out, out_size, "%s/%s", folder, name);
    return (written < 0 || (size_t)written >= out_size) ? -1 : 0;
}

int compute_checksum(const char* filename, uint32_t* result)
{
    if (!filename || !result)
        return -1;

    FILE* f = fopen(filename, "rb");
    if (!f)
    {
        fprintf(stderr, "Cannot open '%s' for checksum: %s\n", filename, strerror(errno));
        return -1;
    }

    uint32_t sum = 0;
    uint8_t buf[CHECKSUM_BUFFER_SIZE + 3];
    size_t carry = 0;
    size_t n;
    while ((n = fread(buf + carry, 1, CHECKSUM_BUFFER_SIZE - carry, f)) > 0)
    {
        n += carry;
        size_t i = 0;
        for (; i + 4 <= n; i += 4)
        {
            uint32_t word = (uint32_t)buf[i] | ((uint32_t)buf[i + 1] << 8) |
                            ((uint32_t)buf[i + 2] << 16) | ((uint32_t)buf[i + 3] << 24);
            sum += word;
        }
        carry = n - i;
        if (carry)
            memmove(buf, buf + i, carry);
    }

    if (ferror(f))
    {
        fprintf(stderr, "Error reading '%s' for checksum.\n", filename);
        fclose(f);
        return -1;
    }
    if (carry)
    {
        uint32_t word = 0;
        for (size_t i = 0; i < carry; i++)
            word |= (uint32_t)buf[i] << (8 * i);
        sum += word;
    }
    if (fclose(f) != 0)
        return -1;

    *result = sum;
    return 0;
}

int is_checksum_file(const char* name)
{
    size_t length = name ? strlen(name) : 0;
    return length > 5 && name[0] == 'V' && strcmp(name + length - 4, ".fex") == 0;
}

static const ImageWTYFileHeader*
find_checksum_target(const ImageWTYHeader* hdr, const ImageWTYFileHeader* files, uint32_t vindex)
{
    const char* target_name = files[vindex].filename + 1;
    uint32_t occurrence = 0;
    for (uint32_t i = 0; i <= vindex; i++)
    {
        if (strcmp(files[i].filename, files[vindex].filename) == 0)
            occurrence++;
    }

    uint32_t found = 0;
    for (uint32_t i = 0; i < hdr->num_files; i++)
    {
        if (strcmp(files[i].filename, target_name) == 0 && ++found == occurrence)
            return &files[i];
    }
    return NULL;
}

static int check_vfiles_common(const char* dump_folder, const ImageWTYHeader* hdr,
                               const ImageWTYFileHeader* files, uint32_t* values)
{
    if (!dump_folder || !hdr || !files)
        return -1;

    int failures = 0;
    for (uint32_t i = 0; i < hdr->num_files; i++)
    {
        const ImageWTYFileHeader* vf = &files[i];
        if (!is_checksum_file(vf->filename))
            continue;

        const ImageWTYFileHeader* target = find_checksum_target(hdr, files, i);
        if (!target)
        {
            fprintf(stderr, "Checksum entry '%s' has no matching payload.\n", vf->filename);
            failures++;
            continue;
        }

        char vpath[1024];
        char target_path[1024];
        const char* vsource = vf->source_path[0] ? vf->source_path : vf->filename;
        const char* source = target->source_path[0] ? target->source_path : target->filename;
        if (join_dump_path(vpath, sizeof(vpath), dump_folder, vsource) != 0 ||
            join_dump_path(target_path, sizeof(target_path), dump_folder, source) != 0)
        {
            fprintf(stderr, "Checksum path is too long or unsafe.\n");
            failures++;
            continue;
        }

        FILE* f = fopen(vpath, "rb");
        uint8_t raw[4];
        if (!f)
        {
            fprintf(stderr, "Cannot open checksum file '%s': %s\n", vpath, strerror(errno));
            failures++;
            continue;
        }
        int read_failed = fread(raw, 1, sizeof(raw), f) != sizeof(raw);
        int close_failed = fclose(f) != 0;
        if (read_failed || close_failed)
        {
            fprintf(stderr, "Cannot read checksum file '%s'.\n", vpath);
            failures++;
            continue;
        }
        uint32_t expected = (uint32_t)raw[0] | ((uint32_t)raw[1] << 8) | ((uint32_t)raw[2] << 16) |
                            ((uint32_t)raw[3] << 24);
        uint32_t actual;
        if (compute_checksum(target_path, &actual) != 0)
        {
            failures++;
            continue;
        }
        if (values)
            values[i] = actual;

        if (actual == expected)
        {
            printf("[OK]   %s checksum matches (%u)\n", source, actual);
            continue;
        }
        if (!values)
        {
            printf("[FAIL] %s checksum mismatch: expected %u, got %u\n", source, expected, actual);
            failures++;
            continue;
        }

        printf("[FIX]  %s checksum will be %u in the output image\n", source, actual);
    }
    return failures ? -1 : 0;
}

int verify_vfiles_checksums(const char* dump_folder, const ImageWTYHeader* hdr,
                            const ImageWTYFileHeader* files)
{
    return check_vfiles_common(dump_folder, hdr, files, NULL);
}

int prepare_vfile_checksums(const char* dump_folder, const ImageWTYHeader* hdr,
                            const ImageWTYFileHeader* files, uint32_t* values)
{
    if (!values)
        return -1;
    return check_vfiles_common(dump_folder, hdr, files, values);
}
