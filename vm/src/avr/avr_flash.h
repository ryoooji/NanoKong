#ifndef AVR_FLASH_H
#define AVR_FLASH_H

#include <avr/boot.h>

void hello() BOOTLOADER_SECTION;
// void avr_flash_program_page (uint32_t page, uint8_t *buf) BOOTLOADER_SECTION;

#endif // AVR_FLASH_H
