/* SPDX-License-Identifier: MIT */

#include <stdarg.h>

#include "types.h"
#include "uart.h"
#include "utils.h"

#define UART_CLOCK 24000000

volatile unsigned int * const UART0DR = (unsigned int *) 0x09000000;
 
void print_uart0(const char *s) {
    while(*s != '\0') { 		/* Loop until end of string */
          s++;			        /* Next char */
    }
}

static u64 uart_base = 0;

int uart_init(void)
{
    return 0;
}

void uart_putbyte(u8 c)
{
    //while (!(read32(uart_base + UTRSTAT) & UTRSTAT_TXBE))
    //    ;

    *UART0DR = (unsigned int)(c); /* Transmit char */
    //write32(uart_base + UTXH, c);
}

u8 uart_getbyte(void)
{
    if (!uart_base)
        return 0;

    //while (!(read32(uart_base + UTRSTAT) & UTRSTAT_RXD))
    //    ;

    return 0;//read32(uart_base + URXH);
}

void uart_putchar(u8 c)
{
    if (c == '\n')
        uart_putbyte('\r');

    uart_putbyte(c);
}

u8 uart_getchar(void)
{
    return uart_getbyte();
}

void uart_puts(const char *s)
{
    while (*s)
        uart_putchar(*(s++));

    uart_putchar('\n');
}

void uart_write(const void *buf, size_t count)
{
    const u8 *p = buf;

    while (count--)
        uart_putbyte(*p++);
}

size_t uart_read(void *buf, size_t count)
{
    u8 *p = buf;
    size_t recvd = 0;

    while (count--) {
        *p++ = uart_getbyte();
        recvd++;
    }

    return recvd;
}

void uart_setbaud(int baudrate)
{
}

void uart_flush(void)
{
}

void uart_clear_irqs(void)
{
}

