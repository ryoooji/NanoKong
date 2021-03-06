//
//  NanoVM, a tiny java VM for the Atmel AVR family
//  Copyright (C) 2005 by Till Harbaum <Till@Harbaum.org>
//
//  This program is free software; you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation; either version 2 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//

//
//  uart.c
//

#ifdef __CC65__
#include <conio.h>
#include <stdio.h>
#endif

#include "types.h"
#include "config.h"
#include "debug.h"

#include "uart.h"
#include "delay.h"
#include "nvmfile.h"

// unix uart emulation
#ifdef UNIX
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <termios.h>
#include <stdio.h>
#include <sys/select.h>

struct termios old_t;

FILE *in = NULL, *out = NULL;

void uart_bye(void) {
#ifdef UART_PORT
  fclose(in);  // out is identical
#else
  // restore terminal settings
  tcsetattr( 0, TCSANOW, &old_t);
#endif
}

void uart_sigproc() {
  exit(-1);   // exit (and thus call uart_bye)
}

void uart_init(void) {
#ifdef UART_PORT
  out = in = fopen(UART_PORT, "w+b");
  if(!in) {
    printf("unable to open %s\n", UART_PORT);
    exit(-1);
  }

#else
  struct termios new_t;

  in = stdin;
  out = stdout;

  if(tcgetattr( 0, &old_t) == -1)
    perror("tcgetattr() failed");

  memcpy( &new_t, &old_t, sizeof(struct termios));

  tcflush( 0, TCIFLUSH);

  // no cr/lf translation
  new_t.c_iflag &= ~(ICRNL);

  // echo and kernel buffers off
  new_t.c_lflag &= ~(ECHO|ICANON);

  tcsetattr( 0, TCSANOW, &new_t);

  // libc buffers off
  setbuf(stdin, NULL);
#endif

  atexit(uart_bye);
  signal(SIGINT, uart_sigproc);
}

void uart_write_byte(u08_t byte) {
  fputc(byte, out);
  fflush(out);
}

u08_t uart_read_byte(void) {
  return fgetc(in);
}

// unix can't tell us how many bytes in the input buffer are,
// so just return one as long as there's data
u08_t uart_available(void) {
  fd_set fds;
  struct timeval tv = { 0, 100 };

  FD_ZERO(&fds);
  FD_SET(fileno(in), &fds);

  return (select(FD_SETSIZE, &fds, NULL, NULL, &tv) == 1)?1:0;
}

#endif  // UNIX

#ifdef AVR
#include <avr/io.h>
#include <avr/interrupt.h>
#define UART_BUFFER_SIZE  (1<<(UART_BUFFER_BITS))
#define UART_BUFFER_MASK  ((UART_BUFFER_SIZE)-1)

// Code from the nvcomm3 branch
// These bits are the same for all UARTS
#define TXEN TXEN0
#define RXEN RXEN0
#define RXCIE RXCIE0
#define UDRE UDRE0
#define USBS USBS0
#define UCPHA UCSZ00
#define UDORD UCSZ01
#define UCPOL UCPOL0
#define U2X U2X0

#if defined(ATMEGA168) || defined(NIBO)
#define UART_COUNT 1
volatile u08_t *UBRRH[] = { &UBRR0H };
volatile u08_t *UBRRL[] = { &UBRR0L };
volatile u08_t *UCSRA[] = { &UCSR0A };
volatile u08_t *UCSRB[] = { &UCSR0B };
volatile u08_t *UCSRC[] = { &UCSR0C };
volatile u08_t *UDR[] = { &UDR0 };
volatile u16_t *UBRR[] = { &UBRR0 };
#elif defined(ATMEGA2560)
#define UART_COUNT 4
volatile u08_t *UBRRH[] = { &UBRR0H, &UBRR1H, &UBRR2H, &UBRR3H };
volatile u08_t *UBRRL[] = { &UBRR0L, &UBRR1L, &UBRR2L, &UBRR3L };
volatile u08_t *UCSRA[] = { &UCSR0A, &UCSR1A, &UCSR2A, &UCSR3A };
volatile u08_t *UCSRB[] = { &UCSR0B, &UCSR1B, &UCSR2B, &UCSR3B };
volatile u08_t *UCSRC[] = { &UCSR0C, &UCSR1C, &UCSR2C, &UCSR3C };
volatile u08_t *UDR[] = { &UDR0, &UDR1, &UDR2, &UDR3 };
volatile u16_t *UBRR[] = { &UBRR0, &UBRR1, &UBRR2, &UBRR3 };
volatile u08_t *XCKDDR[] = { &DDRE, &DDRD, &DDRH, &DDRJ};
volatile u08_t XCKn[] = {DDE2, DDD5, DDH2, DDJ2};
#endif

#if defined(NIBO)
#define URSEL UBRR0H
#endif

u08_t uart_rd[UART_COUNT], uart_wr[UART_COUNT];
u08_t uart_buf[UART_COUNT][UART_BUFFER_SIZE];
u08_t uart_openlog = 0;

// Interrupt handlers for receiving data
// Store byte and increase write pointer
#if defined(USART0_RX_vect)
SIGNAL(USART0_RX_vect) {
  uart_buf[0][uart_wr[0]] = *UDR[0];
  uart_wr[0] = ((uart_wr[0]+1) & UART_BUFFER_MASK);
}
#endif
#if defined(USART1_RX_vect)
SIGNAL(USART1_RX_vect) {
  uart_buf[1][uart_wr[1]] = *UDR[1];
  uart_wr[1] = ((uart_wr[1]+1) & UART_BUFFER_MASK);
}
#endif
#if defined(USART2_RX_vect)
SIGNAL(USART2_RX_vect) {
  uart_buf[2][uart_wr[2]] = *UDR[2];
  uart_wr[2] = ((uart_wr[2]+1) & UART_BUFFER_MASK);
}
#endif
#if defined(USART3_RX_vect)
SIGNAL(USART3_RX_vect) {
  uart_buf[3][uart_wr[3]] = *UDR[3];
  uart_wr[3] = ((uart_wr[3]+1) & UART_BUFFER_MASK);
}
#endif

// four parameters for UART communication
// baudrate, data-bit, parity, stop-bit
void uart_init(u08_t uart, u32_t baudrate) {
  uart_init_impl(uart, baudrate, 1, 0);
}

// Because of the limit of 16 bit 
// the java code transfer the baudrate
// which is 400 times less
u32_t uart_int2baud(u32_t baudrate){
  return baudrate*400;
}

static void uart_set_baudrate(u08_t uart, u32_t baudrate, u08_t factor){
  /* set baud rate by rounding */
  *UBRR[uart] = (CLOCK / (factor>>1) / baudrate - 1) / 2;
}

void uart_init_impl(u08_t uart, u32_t baudrate, u08_t stopbit, u08_t parity){
  //DEBUGF_USART(""DBG32"\n",baudrate);
  // WARNING:
  //    We cannot use more than 15-bit int which is at most 16383
  //    So Baudrate is needed to be considered.
  if (uart_openlog & _BV(uart+1)) uart_close(uart);  // if initialized, then close it
  uart_rd[uart] = uart_wr[uart] = 0;   // init buffers
  bool_t u2x_flag = FALSE;//(baudrate != 57600)?TRUE:FALSE;  // speed up
  u08_t factor = (u2x_flag) ? 8 : 16;

  *UCSRA[uart] = (u2x_flag) ? _BV(U2X) : 0;
  *UCSRB[uart] =
    _BV(RXEN) | _BV(RXCIE) |          // enable receiver and irq
    _BV(TXEN);                        // enable transmitter

  if (stopbit == 2){
    *UCSRC[uart] |= _BV(USBS);
  } else { // default: one stop bit
    *UCSRC[uart] &= ~_BV(USBS);
  }

  switch (parity){
    case 3: // Odd Parity
      *UCSRC[uart] |= _BV(UPM01) | _BV(UPM00);
      break;
    case 2: // Even Parity
      *UCSRC[uart] &= ~_BV(UPM00);
      *UCSRC[uart] |= _BV(UPM01);
      break;
    case 0: // default: No Parity
    default:
      *UCSRC[uart] &= ~(_BV(UPM00) | _BV(UPM01));
      break;
  }

  uart_set_baudrate(uart, baudrate, factor);

#ifdef URSEL // UCSRC shared with UBRRH in nibo
  *UCSRC[uart] |= _BV(URSEL) | _BV(UCSZ00) | _BV(UCSZ01);
#else
  *UCSRC[uart] |= _BV(UCSZ00) | _BV(UCSZ01);  // 8 bit data
#endif // URSEL

  sei();
  uart_openlog |= _BV(uart+1);
}

void uart_native_print(char *str, bool_t ret, u08_t uart){
#ifdef NVM_USE_FLASH_PROGRAM
  u08_t chr;
  // check if source string is within internal nvm file, otherwise 
  // it's directly being read from ram
  if(NVMFILE_ISSET(str)) {
    while((chr = nvmfile_read08(str++)))
      uart_putc(uart, chr);
  } else
#endif // NVM_USE_FLASH_PROGRAM
    while(*str)
      uart_putc(uart, *str++);

  if(ret)
    uart_putc(uart, '\n');
}

void uart_close(u08_t uart){
  *UCSRB[uart] &=
    ~(_BV(RXEN) | _BV(RXCIE) |          // enable receiver and irq
    _BV(TXEN));                        // enable transmitter
  uart_openlog &= ~_BV(uart+1);
}

void uart_spi_init(u08_t uart, u32_t baudrate){
    /* Setting the XCKn port pin as output, enables master mode */
    *XCKDDR[uart] |= _BV(XCKn[uart]);
    /* Set MSPI mode of operation and SPI data mode 0 */
    *UCSRC[uart] |= _BV(UMSEL00) | _BV(UMSEL01) | _BV(UCPHA) | _BV(UCPOL);
    /* Enable receiber and transmitter. */
    *UCSRB[uart] |= _BV(RXEN) | _BV(TXEN);
    /* Set baudrate IMPORTANT: The Baudrate must be set after the transmitter is enabled */
    uart_set_baudrate(uart, baudrate, 2);
    sei();
}

u08_t uart_spi_transfer(u08_t uart, u08_t byte){
  /* Wait for empty transmit buffer */
  while(!(*UCSRA[uart] & _BV(UDRE)));

  // start transmission
  *UDR[uart] = byte;

  /* Wait for data to be received */
  while(!(*UCSRA[uart] & _BV(RXC0)));

  return *UDR[uart];
}

u08_t uart_available(u08_t uart) {
  return(UART_BUFFER_MASK & (uart_wr[uart] - uart_rd[uart]));
}
void uart_flush(u08_t uart){
  uart_wr[uart] = uart_rd[uart];
}
void uart_write_byte(u08_t uart, u08_t byte) {
  /* Wait for empty transmit buffer */
  while(!(*UCSRA[uart] & _BV(UDRE)));

  // asuro needs echo cancellation, since the ir receiver "sees"
  // the transmitter
#ifdef ASURO
  // disable receiver
  *UCSRB[uart] &= ~(_BV(RXEN) | _BV(RXCIE));
#endif

  // start transmission
  *UDR[uart] = byte;

#ifdef ASURO
  // Wait for empty transmit buffer
  while(!(*UCSRA[uart] & _BV(UDRE)));
  delay(MILLISEC(5));

  // re-enable receiver
  *UCSRB[uart] |= _BV(RXEN) | _BV(RXCIE);
#endif
}

u08_t uart_read_byte(u08_t uart) {
  u08_t ret = uart_buf[uart][uart_rd[uart]];

  /* and increase read pointer */
  uart_rd[uart] = ((uart_rd[uart]+1) & UART_BUFFER_MASK);

  return ret;
}

#endif // AVR

#ifdef __CC65__

u08_t uart_available(u08_t uart) {
  return kbhit()?1:0;
}

// Use conio for available() support
u08_t uart_read_byte(u08_t uart) {
  return cgetc();
}

// Use stdio for scrolling support
void uart_putc(u08_t uart, u08_t byte) {
#ifdef __CBM__
  if((byte & 0x60) == 0x40) byte |= 0x80;
  if((byte & 0x60) == 0x60) byte &= 0xDF;
#endif
  putchar(byte);
}

#else // __CC65__

// translate nl to cr nl
void uart_putc(u08_t uart, u08_t byte) {
  if(byte == '\n')
    uart_write_byte(uart, '\r');

  uart_write_byte(uart, byte);
}

#endif // __CC65__
