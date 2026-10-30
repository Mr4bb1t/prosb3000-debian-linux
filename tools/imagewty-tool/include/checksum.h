/**
 * checksum.h
 *
 * Declarations for checksum computation and verification of V*.fex
 * files. Provides functions to ensure file integrity in extracted firmware
 * dumps.
 */

#ifndef CHECKSUM_H
#define CHECKSUM_H

#include <stdint.h>

#include "img_header.h"

/** Return non-zero for entries representing checksums. */
int is_checksum_file(const char* name);

/**
 * @brief Compute a simple 32-bit checksum for a given file.
 *
 * The checksum sums all 4-byte words in little-endian order,
 * padding any remaining bytes with zeros.
 *
 * @param filename Path to the file.
 * @param result Receives the calculated checksum on success.
 * @return 0 on success, non-zero on error.
 */
int compute_checksum(const char* filename, uint32_t* result);

/**
 * @brief Calculate replacement V-file checksums without modifying the dump.
 *
 * @param dump_folder Path to folder containing extracted files.
 * @param hdr Image header containing the number of entries.
 * @param files File entries and their local source paths.
 * @param values Array of hdr->num_files values, indexed by checksum entry.
 * @return 0 when all checksum entries and targets were read successfully.
 */
int prepare_vfile_checksums(const char* dump_folder, const ImageWTYHeader* hdr,
                            const ImageWTYFileHeader* files, uint32_t* values);

/**
 * @brief Verify "V*.fex" checksums without updating them.
 *
 * Useful for integrity check after extraction.
 *
 * @param dump_folder Path to folder containing extracted files.
 * @param hdr Image header containing the number of entries.
 * @param files File entries and their local source paths.
 * @return 0 when every checksum matches, non-zero otherwise.
 */
int verify_vfiles_checksums(const char* dump_folder, const ImageWTYHeader* hdr,
                            const ImageWTYFileHeader* files);

#endif /* CHECKSUM_H */
