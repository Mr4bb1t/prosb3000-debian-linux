/**
 * @file img_header.c
 * @brief Implements reading of IMAGEWTY image headers and file headers.
 */

#include "img_header.h"

#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

/**
 * @brief Read a 32-bit unsigned integer from a file in little-endian format.
 *
 * @param f   File pointer.
 * @param out Pointer to store the result.
 * @return 0 on success, -1 on read failure.
 */
static int read_uint32_le(FILE* f, uint32_t* out)
{
    uint8_t buf[4];
    if (fread(buf, 1, 4, f) != 4)
    {
        return -1;
    }
    *out = ((uint32_t)buf[0]) | ((uint32_t)buf[1] << 8) | ((uint32_t)buf[2] << 16) |
           ((uint32_t)buf[3] << 24);
    return 0;
}

/**
 * @brief Read the global IMAGEWTY header from the image file.
 *
 * @param f   File pointer to IMAGEWTY file.
 * @param hdr Pointer to ImageWTYHeader structure to populate.
 * @return 0 on success, -1 on read failure.
 */
int read_image_header(FILE* f, ImageWTYHeader* hdr)
{
    if (fread(hdr->magic, 1, 8, f) != 8)
    {
        fprintf(stderr, "Failed to read IMAGEWTY magic\n");
        return -1;
    }
    hdr->magic[8] = '\0'; /* Null-terminate magic string */

    if (read_uint32_le(f, &hdr->header_version) != 0 || read_uint32_le(f, &hdr->header_size) != 0 ||
        read_uint32_le(f, &hdr->base_ram) != 0 || read_uint32_le(f, &hdr->format_version) != 0 ||
        read_uint32_le(f, &hdr->total_image_size) != 0 ||
        read_uint32_le(f, &hdr->header_size_aligned) != 0 ||
        read_uint32_le(f, &hdr->file_header_length) != 0 ||
        read_uint32_le(f, &hdr->usb_product_id) != 0 ||
        read_uint32_le(f, &hdr->usb_vendor_id) != 0 || read_uint32_le(f, &hdr->hardware_id) != 0 ||
        read_uint32_le(f, &hdr->firmware_id) != 0 || read_uint32_le(f, &hdr->unknown1) != 0 ||
        read_uint32_le(f, &hdr->unknown2) != 0 || read_uint32_le(f, &hdr->num_files) != 0 ||
        read_uint32_le(f, &hdr->unknown3) != 0)
    {
        fprintf(stderr, "Failed to read IMAGEWTY header fields\n");
        return -1;
    }

    return 0;
}

/**
 * @brief Read a single file header from the image file.
 *
 * @param f                  File pointer to IMAGEWTY file.
 * @param fh                 Pointer to ImageWTYFileHeader structure to populate.
 * @param file_header_length Length of each file header in bytes.
 * @return 0 on success, -1 on read failure.
 */
int read_file_header(FILE* f, ImageWTYFileHeader* fh, uint32_t file_header_length)
{
    if (!f || !fh || file_header_length < IMAGEWTY_FILE_HEADER_MIN_SIZE ||
        file_header_length > IMAGEWTY_FILE_HEADER_MAX_SIZE)
    {
        fprintf(stderr, "Invalid file header length: %u\n", file_header_length);
        return -1;
    }

    memset(fh, 0, sizeof(*fh));
    off_t start_offset = ftello(f);
    if (start_offset < 0)
    {
        perror("Failed to get file-header offset");
        return -1;
    }

    /* Basic header fields */
    if (read_uint32_le(f, &fh->filename_length) != 0 || read_uint32_le(f, &fh->header_size) != 0)
    {
        fprintf(stderr, "Failed to read file header basic fields\n");
        return -1;
    }

    /* Read maintype (8 bytes) */
    if (fread(fh->maintype, 1, 8, f) != 8)
    {
        fprintf(stderr, "Failed to read maintype\n");
        return -1;
    }
    fh->maintype[8] = '\0';

    /* Read subtype (16 bytes) */
    if (fread(fh->subtype, 1, 16, f) != 16)
    {
        fprintf(stderr, "Failed to read subtype\n");
        return -1;
    }
    fh->subtype[16] = '\0';

    if (read_uint32_le(f, &fh->unknown0) != 0)
    {
        fprintf(stderr, "Failed to read file header unknown0\n");
        return -1;
    }

    /* Read filename (up to 256 bytes) */
    if (fh->filename_length == 0 || fh->filename_length > 256)
    {
        fprintf(stderr, "Invalid filename field length: %u\n", fh->filename_length);
        return -1;
    }
    if (fread(fh->filename, 1, fh->filename_length, f) != fh->filename_length)
    {
        fprintf(stderr, "Failed to read filename\n");
        return -1;
    }
    fh->filename[fh->filename_length] = '\0';

    /* Skip remaining filename padding */
    if (fseeko(f, (off_t)(256 - fh->filename_length), SEEK_CUR) != 0)
    {
        perror("Failed to skip filename padding");
        return -1;
    }

    /* File size fields */
    if (read_uint32_le(f, &fh->stored_length) != 0 || read_uint32_le(f, &fh->pad1) != 0 ||
        read_uint32_le(f, &fh->original_length) != 0 || read_uint32_le(f, &fh->pad2) != 0 ||
        read_uint32_le(f, &fh->offset) != 0)
    {
        fprintf(stderr, "Failed to read file header size fields\n");
        return -1;
    }

    /* Skip any remaining padding in the file header */
    off_t current_offset = ftello(f);
    if (current_offset < 0)
    {
        perror("Failed to get file-header position");
        return -1;
    }
    off_t consumed = current_offset - start_offset;
    off_t skip = (off_t)file_header_length - consumed;
    if (skip > 0)
    {
        if (fseeko(f, skip, SEEK_CUR) != 0)
        {
            perror("Failed to skip file-header padding");
            return -1;
        }
    }

    return 0;
}

/**
 * @brief Read all file headers from the image.
 *
 * @param f               File pointer to IMAGEWTY file.
 * @param num_files       Number of files in the image.
 * @param file_header_length Length of each file header in bytes.
 * @return Pointer to allocated array of ImageWTYFileHeader structures, or NULL on error.
 */
ImageWTYFileHeader* read_all_file_headers(FILE* f, uint32_t num_files, uint32_t file_header_length)
{
    if (num_files == 0 || num_files > MAX_IMAGE_FILES ||
        file_header_length < IMAGEWTY_FILE_HEADER_MIN_SIZE ||
        file_header_length > IMAGEWTY_FILE_HEADER_MAX_SIZE)
    {
        fprintf(stderr, "Error: invalid header table dimensions: files=%u, entry_size=%u.\n",
                num_files, file_header_length);
        return NULL;
    }

    ImageWTYFileHeader* files = malloc(sizeof(ImageWTYFileHeader) * num_files);
    if (!files)
    {
        perror("Failed to allocate memory for file headers");
        return NULL;
    }

    for (uint32_t i = 0; i < num_files; i++)
    {
        uint64_t position = (uint64_t)FILE_HEADERS_START + (uint64_t)i * file_header_length;
        if (position > INT64_MAX || fseeko(f, (off_t)position, SEEK_SET) != 0)
        {
            perror("Failed to seek to file header");
            free(files);
            return NULL;
        }
        if (read_file_header(f, &files[i], file_header_length) != 0)
        {
            fprintf(stderr, "Failed to read file header %u\n", i);
            free(files);
            return NULL;
        }
    }

    return files;
}

int is_safe_dump_name(const char* name)
{
    if (!name || !*name || strcmp(name, ".") == 0 || strcmp(name, "..") == 0)
        return 0;

    for (const unsigned char* p = (const unsigned char*)name; *p; p++)
    {
        if (*p == '/' || *p == '\\' || *p == '"' || iscntrl(*p))
            return 0;
    }
    return 1;
}

int validate_image_layout(FILE* f, const ImageWTYHeader* hdr, const ImageWTYFileHeader* files)
{
    if (!f || !hdr || !files || memcmp(hdr->magic, IMAGEWTY_MAGIC, 8) != 0)
        return -1;
    if (hdr->header_size < 68 || hdr->header_size > IMG_HEADER_HEADER_SIZE || hdr->num_files == 0 ||
        hdr->num_files > MAX_IMAGE_FILES ||
        hdr->file_header_length < IMAGEWTY_FILE_HEADER_MIN_SIZE ||
        hdr->file_header_length > IMAGEWTY_FILE_HEADER_MAX_SIZE)
    {
        fprintf(stderr, "Error: invalid IMAGEWTY header dimensions.\n");
        return -1;
    }

    off_t saved = ftello(f);
    if (saved < 0 || fseeko(f, 0, SEEK_END) != 0)
    {
        perror("Error determining image size");
        return -1;
    }
    off_t end = ftello(f);
    if (end < 0 || fseeko(f, saved, SEEK_SET) != 0)
    {
        perror("Error determining image size");
        return -1;
    }
    uint64_t physical_size = (uint64_t)end;
    uint64_t table_end =
        (uint64_t)FILE_HEADERS_START + (uint64_t)hdr->num_files * hdr->file_header_length;
    if (table_end > physical_size)
    {
        fprintf(stderr, "Error: file-header table extends beyond the image.\n");
        return -1;
    }

    for (uint32_t i = 0; i < hdr->num_files; i++)
    {
        const ImageWTYFileHeader* fh = &files[i];
        uint64_t data_end = (uint64_t)fh->offset + fh->stored_length;
        if (!is_safe_dump_name(fh->filename) || fh->filename_length == 0 ||
            fh->filename_length > 256 || fh->header_size < IMAGEWTY_FILE_HEADER_MIN_SIZE ||
            fh->original_length > fh->stored_length || fh->offset < table_end ||
            data_end > physical_size)
        {
            fprintf(stderr, "Error: invalid file entry %u ('%s').\n", i + 1, fh->filename);
            return -1;
        }
    }
    return 0;
}
