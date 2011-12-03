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
//  native_avr.c
//

#include "types.h"
#include "debug.h"
#include "config.h"
#include "error.h"

#ifndef CTBOT
#ifndef NIBO
#ifdef AVR

#include "vm.h"
#include "native.h"
#include "native_avr.h"
#include "native_stdio.h"
#include "stack.h"
#include "uart.h"

#include <avr/io.h>
#include <avr/interrupt.h>

#if defined(ATMEGA128)
volatile u08_t *ports[] = { &PORTA, &PORTB, &PORTC, &PORTD, &PORTE, &PORTF };
volatile u08_t *ddrs[]  = { &DDRA,  &DDRB,  &DDRC,  &DDRD,  &DDRE,  &DDRF  };
volatile u08_t *pins[]  = { &PINA,  &PINB,  &PINC,  &PIND,  &PINE,  &PINF  };

#elif defined(ATMEGA2560)
volatile u08_t *ports[] = { &PORTA, &PORTB, &PORTC, &PORTD, &PORTE, &PORTF, &PORTG, &PORTH, &PORTJ, &PORTK, &PORTL};
volatile u08_t *ddrs[]  = { &DDRA,  &DDRB,  &DDRC,  &DDRD,  &DDRE,  &DDRF,  &DDRG,  &DDRH,  &DDRJ,  &DDRK,  &DDRL };
volatile u08_t *pins[]  = { &PINA,  &PINB,  &PINC,  &PIND,  &PINE,  &PINF,  &PING,  &PINH,  &PINJ,  &PINK,  &PINL };

#elif defined(ATMEGA32)
volatile u08_t *ports[] = { &PORTA, &PORTB, &PORTC, &PORTD };
volatile u08_t *ddrs[]  = { &DDRA,  &DDRB,  &DDRC,  &DDRD  };
volatile u08_t *pins[]  = { &PINA,  &PINB,  &PINC,  &PIND  };

#elif defined(ATMEGA8)
volatile u08_t *ports[] = { NULL,  &PORTB, &PORTC, &PORTD  };
volatile u08_t *ddrs[]  = { NULL,   &DDRB,  &DDRC,  &DDRD  };
volatile u08_t *pins[]  = { NULL,   &PINB,  &PINC,  &PIND  };

#elif defined(ATMEGA168)
volatile u08_t *ports[] = { NULL,  &PORTB, &PORTC, &PORTD  };
volatile u08_t *ddrs[]  = { NULL,   &DDRB,  &DDRC,  &DDRD  };
volatile u08_t *pins[]  = { NULL,   &PINB,  &PINC,  &PIND  };

#else
#error "Unsupported AVR CPU!"
#endif

volatile static nvm_int_t ticks;
#ifndef ATMEGA2560
SIGNAL(SIG_OUTPUT_COMPARE1A) {
  TCNT1 = 0;
  ticks++;
}
#else
ISR(TIMER1_COMPA_vect)
{
  TCNT1 = 0;
  ticks++;
}
ISR(INT0_vect)
{
	PORTA= ~PORTA;
}
ISR(PCINT0_vect)
{
	PORTA= ~PORTA;
}
#endif

void native_init(void) {
  // init timer
#if defined(ATMEGA168) 
  TCCR1B = _BV(CS11);           // clk/8
  OCR1A = (u16_t)(CLOCK/800u);  // 100 Hz is default
  TIMSK1 |= _BV(OCIE1A);         // interrupt on compare
#elif defined(ATMEGA2560)
  TCCR1B &= ~(_BV(CS12) | _BV(CS11) | _BV(CS10));
  TCCR1B |= _BV(CS11);
  TIMSK1 = _BV(OCIE1A);		//output compare interrupt enable
  OCR1A = 2000;			//set default T=1ms

  //INT0.PCINT0 interrupt test
  EIMSK=_BV(INT0);
  PCICR=_BV(PCIE0);
  PCMSK0=_BV(PCINT0);
#else
  TCCR1B = _BV(CS11);           // clk/8
  OCR1A = (u16_t)(CLOCK/800u);  // 100 Hz is default
  TIMSK |= _BV(OCIE1A);         // interrupt on compare
#endif

  sei();
}

// the AVR class
void native_avr_avr_invoke(u08_t mref) {
  if(mref == NATIVE_METHOD_GETCLOCK) {
    stack_push(CLOCK/1000);
  } else
    error(ERROR_NATIVE_UNKNOWN_METHOD);
}

// the USART class
void native_avr_usart_invoke(u08_t mref) {
  char tmp[8];
  if(mref == NATIVE_METHOD_USART_PRINTLN_STR) {
    char *addr = stack_pop_addr();
    u08_t uart = stack_pop();
    uart_native_print(addr, TRUE, uart);
  } else if(mref == NATIVE_METHOD_USART_PRINTLN_INT) {
    native_itoa((char*)tmp, stack_pop_int());
    u08_t uart = stack_pop();
    uart_native_print(tmp, TRUE, uart);
  } else if(mref == NATIVE_METHOD_USART_PRINT_STR) {
    char *addr = stack_pop_addr();
    u08_t uart = stack_pop();
    uart_native_print(addr, FALSE, uart);
  } else if(mref == NATIVE_METHOD_USART_PRINT_INT) {
    native_itoa((char*)tmp, stack_pop_int());
    u08_t uart = stack_pop();
    uart_native_print(tmp, FALSE, uart);
  } else if(mref == NATIVE_METHOD_USART_PRINTLN_CHAR) {
    u08_t c = stack_pop_int();
    u08_t uart = stack_pop();
    uart_putc(uart, c);
    uart_putc(uart, '\n');
  } else if(mref == NATIVE_METHOD_USART_PRINT_CHAR) {
    u08_t c = stack_pop_int();
    u08_t uart = stack_pop();
    //DEBUGF_USART(""DBG16"\n",c);
    //DEBUGF_USART(""DBG16"\n",uart);
    uart_putc(uart, c);
#ifdef NVM_USE_EXT_STDIO
  } else if(mref == NATIVE_METHOD_USART_FORMAT) {
    char *addr = stack_pop_addr();
    stack_pop_int(); // TODO
    u08_t uart = stack_pop();
    uart_native_print(addr, FALSE, uart);
    stack_push(stack_peek(0)); // duplicate this ref
#endif    
  } else if (mref == NATIVE_METHOD_USART_AVAILABLE) {
    u08_t uart = stack_pop();
    stack_push(uart_available(uart));
  } else if(mref == NATIVE_METHOD_USART_READ) {
    u08_t uart = stack_pop();
    stack_push(uart_read_byte(uart));
  } else if (mref == NATIVE_METHOD_USART_INIT) {
    u08_t parity = stack_pop();
    u08_t stopbit = stack_pop();
    u32_t baudrate = stack_pop_int();
    u08_t uart = stack_pop();
    baudrate = uart_int2baud(baudrate);
    uart_init_impl(uart, baudrate, stopbit, parity);
  } else
    error(ERROR_NATIVE_UNKNOWN_METHOD);
 
}

// the port class
void native_avr_port_invoke(u08_t mref) {
  if(mref == NATIVE_METHOD_SETINPUT) {
    u08_t bit  = stack_pop();
    u08_t port = stack_pop();
    DEBUGF("native setinput %bd/%bd\n", port, bit);
    *ddrs[port] &= ~_BV(bit);
  } else if(mref == NATIVE_METHOD_SETOUTPUT) {
    u08_t bit  = stack_pop();
    u08_t port = stack_pop();
    DEBUGF("native setoutput %bd/%bd\n", port, bit);
    *ddrs[port] |= _BV(bit);
  } else if(mref == NATIVE_METHOD_SETBIT) {
    u08_t bit  = stack_pop();
    u08_t port = stack_pop();
    DEBUGF("native setbit %bd/%bd\n", port, bit);
    *ports[port] |= _BV(bit);
  } else if(mref == NATIVE_METHOD_CLRBIT) {
    u08_t bit  = stack_pop();
    u08_t port = stack_pop();
    DEBUGF("native clrbit %bd/%bd\n", port, bit);
    *ports[port] &= ~_BV(bit);
  } else if(mref == NATIVE_METHOD_GETINPUT) {
    u08_t bit  = stack_pop();
    u08_t port = stack_pop();
    DEBUGF("native clrbit %bd/%bd\n", port, bit);
    stack_push( (*pins[port]>>bit) & 0x01);
  } else
    error(ERROR_NATIVE_UNKNOWN_METHOD);
}

// the timer class, based on AVR 16 bit timer 1
void native_avr_timer_invoke(u08_t mref) {
  if(mref == NATIVE_METHOD_SETSPEED) {
    OCR1A = stack_pop();  // set reload value
    TCNT1 = 0;
  } else if(mref == NATIVE_METHOD_GET) {
    stack_push(ticks);
  } else if(mref == NATIVE_METHOD_TWAIT) {
    nvm_int_t wait = stack_pop();
    ticks = 0;
    while(ticks < wait);      // reset watchdog here if enabled
  } else if(mref == NATIVE_METHOD_SETPRESCALER) {
    TCCR1B = stack_pop();
  } else
    error(ERROR_NATIVE_UNKNOWN_METHOD);
}

// the Adc class
void native_avr_adc_invoke(u08_t mref) {
  if(mref == NATIVE_METHOD_ADC_SETPRESCALER) {
    ADCSRA = _BV(ADEN) | (stack_pop_int() & 7);  // set prescaler value
  } else if(mref == NATIVE_METHOD_ADC_SETREFERENCE) {
    ADMUX = stack_pop_int() & 0xc0;              // set reference value
  } else if(mref == NATIVE_METHOD_ADC_GETVALUE) {
    // ADLAR = 0
    ADMUX = (ADMUX & 0xc0) | (stack_pop_int() & 0x0f);

    // do conversion
    ADCSRA |= _BV(ADSC);                  // Start conversion
    while(!(ADCSRA & _BV(ADIF)));         // wait for conversion complete
    ADCSRA |= _BV(ADIF);                  // clear ADCIF
    stack_push(ADCL + (ADCH << 8));
  } else if(mref == NATIVE_METHOD_ADC_GETBYTE) {
    // ADLAR = 1
    ADMUX = (ADMUX & 0xc0) | _BV(ADLAR) | (stack_pop_int() & 0x0f);

    // do conversion
    ADCSRA |= _BV(ADSC);                  // Start conversion
    while(!(ADCSRA & _BV(ADIF)));         // wait for conversion complete
    ADCSRA |= _BV(ADIF);                  // clear ADCIF
    stack_push(ADCH);
  } else
    error(ERROR_NATIVE_UNKNOWN_METHOD);
}

// the Pwm class
#if (!defined(ATMEGA8) && !defined(ATMEGA168) && !defined(ATMEGA32)) && !defined(ATMEGA2560)
#error Please add PWM support for your CPU!
#endif

void native_avr_pwm_invoke(u08_t mref) {
  if(mref == NATIVE_METHOD_PWM_SETPRESCALER) {
    u08_t value = stack_pop();
    u08_t port = stack_pop();   // top byte contains class ref

    // implement pwm1
    if(port == 0 || port==1) {
      // keep everything but prescaler
#if defined(ATMEGA168) || defined(ATMEGA2560)
      TCCR2B = (TCCR2B & ~7) | (value & 7);
#else
      TCCR2 = (TCCR2 & ~7) | (value & 7);
#endif
    }

  } else if(mref == NATIVE_METHOD_PWM_SETRATIO) {
    u08_t value = stack_pop();
    u08_t port = stack_pop();   // top byte contains class ref

    // implement pwm0.pwm1
    if(port == 0 || port ==1) {

      // setup of timer 2: keep prescaler, set fast pwm
      // and clear OC2 on match, set OC2 on top
#if defined(ATMEGA168) || defined(ATMEGA2560)
      TCCR2A = _BV(WGM21) | _BV(WGM20) | _BV(COM2A1) | _BV(COM2B1);
      TCCR2B = (TCCR2B & 7) ;
#else
      TCCR2 = (TCCR2 & 7) | _BV(WGM21) | _BV(WGM20) | _BV(COM21);
#endif

#if defined(ATMEGA8)
      // the pwm output is on pin b.3 on the mega8
      DDRB |= _BV(3);        // OC2 -> output
#elif defined(ATMEGA168)
      // the pwm output is on pin b.3 on the mega8
      DDRB |= _BV(3);        // OC2 -> output
#elif defined(ATMEGA32)
      // the pwm output is on pin d.7 on the mega32
      DDRD |= _BV(7);        // OC2 -> output
#elif defined(ATMEGA128)
      // the pwm output is on pin b.7 on the mega128
      DDRB |= _BV(7);        // OC2 -> output
#elif defined(ATMEGA2560)
      // the pwm output is on pin b.4, h.6 on the mega2560
      if(port==0)
      	DDRB |= _BV(4);        // OC2A -> output
      else if(port==1)
      	DDRH |= _BV(6);        // OC2B -> output
#else
#error Please add PWM support for your CPU!
#endif

#if defined(ATMEGA168) || defined(ATMEGA2560)
      if(port==0)
	OCR2A = value;
      else if(port==1)
	OCR2B = value;
#else
      OCR2 = value;
#endif
    }
  } else
    error(ERROR_NATIVE_UNKNOWN_METHOD);
}

#endif

#endif // !NIBO
#endif // !CTBOT
