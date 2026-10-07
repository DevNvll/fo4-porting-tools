/* liboodle-data-shared.so for Linux: OodleLZ_Decompress of the Windows library oo2core_9_win64.dll.
 *
 *   gcc -O2 -fPIC -shared -o liboodle-data-shared.so oodle9.c
 *
 * tiger-pkg loads `liboodle-data-shared.so` for a game with Oodle 9 (Marathon). The game has only
 * the Windows library. This file loads that library into the process: it maps its sections,
 * applies its relocations, gives each of its 41 imports a small function, and runs its start
 * code. The shim of tiger-pkg for Oodle 3 (liblinoodle3.so) cannot do this: the start code of
 * this library reads the thread block of Windows (the segment register GS), which that shim
 * leaves empty.
 *
 * The library is the file that OODLE9_DLL names, else oo2core_9_win64.dll or
 * oo2core_3_win64.dll in the working folder. It is a file of the game: it is not here.
 *
 * Each import has the calling convention of Windows (ms_abi). On Linux the register GS is
 * free (glibc uses FS), so each call sets GS to a block with the three fields that the
 * library reads, and puts the old value back.
 */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <asm/prctl.h>

#define MS __attribute__((ms_abi))

static int debug(void) { return getenv("OODLE9_DEBUG") != NULL; }

/* ---- the imports ---- */
static MS void k_OutputDebugStringA(const char *s) { if (debug()) fprintf(stderr, "[oodle9] %s", s); }
static MS void *k_HeapAlloc(void *heap, uint32_t flags, size_t size) { return (flags & 8) ? calloc(1, size) : malloc(size); }
static MS int k_HeapFree(void *heap, uint32_t flags, void *p) { free(p); return 1; }
static MS void *k_GetProcessHeap(void) { return (void *)0x10000; }
static MS int k_DisableThreadLibraryCalls(void *module) { return 1; }
static MS void k_GetSystemTimeAsFileTime(uint64_t *out) {
    struct timespec t; clock_gettime(CLOCK_REALTIME, &t);
    *out = ((uint64_t)t.tv_sec + 11644473600ULL) * 10000000ULL + (uint64_t)t.tv_nsec / 100;
}
static MS uint32_t k_GetCurrentThreadId(void) { return (uint32_t)syscall(SYS_gettid); }
static MS uint32_t k_GetCurrentProcessId(void) { return (uint32_t)getpid(); }
static MS int k_QueryPerformanceCounter(int64_t *out) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    *out = (int64_t)t.tv_sec * 1000000000LL + t.tv_nsec; return 1;
}
static MS int k_IsDebuggerPresent(void) { return 0; }
/* 10: SSE2. Each other feature: not there (the start code asks for 23, fast fail). */
static MS int k_IsProcessorFeaturePresent(uint32_t feature) { return feature == 10; }
static MS int k_TerminateProcess(void *process, uint32_t code) { fprintf(stderr, "[oodle9] the library stopped the process (%u)\n", code); abort(); }
static MS void *k_GetCurrentProcess(void) { return (void *)-1; }
static MS void *k_SetUnhandledExceptionFilter(void *f) { return NULL; }
static MS int32_t k_UnhandledExceptionFilter(void *info) { return 0; }
static MS void *k_RtlVirtualUnwind(void) { return NULL; }
static MS void *k_RtlLookupFunctionEntry(void) { return NULL; }
static MS void k_RtlCaptureContext(void *context) { memset(context, 0, 0x4D0); }
static MS void k_InitializeSListHead(void *head) { memset(head, 0, 16); }

static MS void *v_memmove(void *d, const void *s, size_t n) { return memmove(d, s, n); }
static MS void *v_memcpy(void *d, const void *s, size_t n) { return memcpy(d, s, n); }
static MS void *v_memset(void *d, int c, size_t n) { return memset(d, c, n); }
static MS void v_fatal(void) { fprintf(stderr, "[oodle9] the library called a function for an error\n"); abort(); }
static MS void v_nothing(void) { }
static MS void *v_null(void) { return NULL; }
static MS int v_zero(void) { return 0; }

typedef MS void (*init_fn)(void);
typedef MS int (*init_e_fn)(void);
static MS void c_initterm(init_fn *first, init_fn *last) { for (; first < last; first++) if (*first) (*first)(); }
static MS int c_initterm_e(init_e_fn *first, init_e_fn *last) {
    for (; first < last; first++) if (*first) { int r = (*first)(); if (r) return r; }
    return 0;
}
static MS void c_free(void *p) { free(p); }

static const struct { const char *name; void *function; } IMPORTS[] = {
    {"OutputDebugStringA", k_OutputDebugStringA}, {"HeapAlloc", k_HeapAlloc}, {"HeapFree", k_HeapFree},
    {"GetProcessHeap", k_GetProcessHeap}, {"DisableThreadLibraryCalls", k_DisableThreadLibraryCalls},
    {"GetSystemTimeAsFileTime", k_GetSystemTimeAsFileTime}, {"GetCurrentThreadId", k_GetCurrentThreadId},
    {"GetCurrentProcessId", k_GetCurrentProcessId}, {"QueryPerformanceCounter", k_QueryPerformanceCounter},
    {"IsDebuggerPresent", k_IsDebuggerPresent}, {"IsProcessorFeaturePresent", k_IsProcessorFeaturePresent},
    {"TerminateProcess", k_TerminateProcess}, {"GetCurrentProcess", k_GetCurrentProcess},
    {"SetUnhandledExceptionFilter", k_SetUnhandledExceptionFilter}, {"UnhandledExceptionFilter", k_UnhandledExceptionFilter},
    {"RtlVirtualUnwind", k_RtlVirtualUnwind}, {"RtlLookupFunctionEntry", k_RtlLookupFunctionEntry},
    {"RtlCaptureContext", k_RtlCaptureContext}, {"InitializeSListHead", k_InitializeSListHead},
    {"memmove", v_memmove}, {"memcpy", v_memcpy}, {"memset", v_memset},
    {"_purecall", v_fatal}, {"__std_terminate", v_fatal}, {"terminate", v_fatal},
    {"__std_type_info_destroy_list", v_nothing}, {"__current_exception_context", v_null}, {"__current_exception", v_null},
    {"__C_specific_handler", v_fatal}, {"__CxxFrameHandler3", v_fatal},
    {"_initialize_narrow_environment", v_zero}, {"_initterm_e", c_initterm_e}, {"_initterm", c_initterm},
    {"_cexit", v_nothing}, {"_crt_atexit", v_zero}, {"_execute_onexit_table", v_zero},
    {"_register_onexit_function", v_zero}, {"_initialize_onexit_table", v_zero}, {"_configure_narrow_argv", v_zero},
    {"_seh_filter_dll", v_zero}, {"free", c_free},
};

/* ---- the thread block ---- */
struct block { uint64_t field[64]; };          /* 0x08 stack base, 0x10 stack limit, 0x30 the block itself */
static __thread struct block tib;

static unsigned long enter(void) {
    unsigned long old = 0;
    syscall(SYS_arch_prctl, ARCH_GET_GS, &old);
    if (!tib.field[6]) {
        uint64_t here = (uint64_t)&old;
        tib.field[1] = here + 0x10000;         /* near the top of this stack; the library uses it as an id only */
        tib.field[2] = here - 0x100000;
        tib.field[6] = (uint64_t)&tib;
    }
    syscall(SYS_arch_prctl, ARCH_SET_GS, &tib);
    return old;
}
static void leave(unsigned long old) { syscall(SYS_arch_prctl, ARCH_SET_GS, old); }

/* ---- the loader ---- */
static uint8_t *image;
typedef MS int64_t (*decompress_fn)(const void *, int64_t, void *, int64_t, int32_t, int32_t, int32_t,
                                    void *, int64_t, void *, void *, void *, int64_t, int32_t);
static decompress_fn decompress;
static pthread_once_t once = PTHREAD_ONCE_INIT;

static uint32_t u32(const uint8_t *p) { uint32_t v; memcpy(&v, p, 4); return v; }
static uint16_t u16(const uint8_t *p) { uint16_t v; memcpy(&v, p, 2); return v; }

static void fail(const char *text) { fprintf(stderr, "[oodle9] %s\n", text); }

static void load(void) {
    const char *names[] = { getenv("OODLE9_DLL"), "oo2core_9_win64.dll", "oo2core_3_win64.dll" };
    FILE *f = NULL;
    for (int i = 0; i < 3 && !f; i++) if (names[i]) f = fopen(names[i], "rb");
    if (!f) { fail("oo2core_9_win64.dll is not in the working folder; OODLE9_DLL can name it"); return; }
    fseek(f, 0, SEEK_END); long size = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *file = malloc(size);
    if (fread(file, 1, size, f) != (size_t)size) { fail("cannot read the library"); fclose(f); return; }
    fclose(f);
    const uint8_t *nt = file + u32(file + 0x3C);
    if (u16(file) != 0x5A4D || u32(nt) != 0x4550 || u16(nt + 4) != 0x8664 || u16(nt + 24) != 0x20B) {
        fail("the file is not a Windows library for x86-64"); return;
    }
    int sections = u16(nt + 6);
    const uint8_t *optional = nt + 24, *section = optional + u16(nt + 20);
    uint64_t base; memcpy(&base, optional + 24, 8);
    uint32_t image_size = u32(optional + 56), headers = u32(optional + 60), entry = u32(optional + 16);
    image = mmap(NULL, image_size, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (image == MAP_FAILED) { image = NULL; fail("no memory for the library"); return; }
    memcpy(image, file, headers);
    const uint8_t *dirs = image + (optional - file) + 112;  /* the data directories, in the copy of the headers */
    for (int i = 0; i < sections; i++, section += 40) {
        uint32_t address = u32(section + 12), raw_size = u32(section + 16), raw = u32(section + 20), virtual_size = u32(section + 8);
        if (raw_size) memcpy(image + address, file + raw, raw_size < virtual_size || !virtual_size ? raw_size : virtual_size);
    }
    free(file);
    /* relocations (directory 5): each block has a page address, a size and 16-bit entries; type 10 is a 64-bit address */
    uint32_t at = u32(dirs + 5 * 8), end = at + u32(dirs + 5 * 8 + 4);
    int64_t delta = (int64_t)((uint64_t)image - base);
    while (at < end) {
        uint32_t page = u32(image + at), block = u32(image + at + 4);
        if (!block) break;
        for (uint32_t i = 8; i + 2 <= block; i += 2) {
            uint16_t e = u16(image + at + i);
            if ((e >> 12) == 10) { uint64_t v; memcpy(&v, image + page + (e & 0xFFF), 8); v += delta; memcpy(image + page + (e & 0xFFF), &v, 8); }
            else if ((e >> 12) != 0) { fail("the library has a relocation of an unknown type"); return; }
        }
        at += block;
    }
    /* imports (directory 1): 20 bytes for each library, then a table of names */
    for (uint8_t *d = image + u32(dirs + 8); u32(d + 12); d += 20) {
        uint64_t *names = (uint64_t *)(image + (u32(d) ? u32(d) : u32(d + 16)));
        uint64_t *slots = (uint64_t *)(image + u32(d + 16));
        for (; *names; names++, slots++) {
            const char *name = (*names >> 63) ? "(ordinal)" : (const char *)(image + (uint32_t)*names + 2);
            void *function = NULL;
            for (size_t i = 0; i < sizeof(IMPORTS) / sizeof(IMPORTS[0]); i++)
                if (!strcmp(IMPORTS[i].name, name)) function = IMPORTS[i].function;
            if (!function) { fprintf(stderr, "[oodle9] the library imports %s, which this file does not have\n", name); return; }
            *slots = (uint64_t)function;
        }
    }
    /* the start code: DllMain(module, DLL_PROCESS_ATTACH, NULL) */
    unsigned long old = enter();
    int ok = ((MS int (*)(void *, uint32_t, void *))(image + entry))(image, 1, NULL);
    leave(old);
    if (!ok) { fail("the start code of the library failed"); return; }
    /* exports (directory 0) */
    const uint8_t *e = image + u32(dirs);
    uint32_t count = u32(e + 24);
    const uint8_t *functions = image + u32(e + 28), *name_table = image + u32(e + 32), *ordinals = image + u32(e + 36);
    for (uint32_t i = 0; i < count; i++)
        if (!strcmp((const char *)(image + u32(name_table + i * 4)), "OodleLZ_Decompress"))
            decompress = (decompress_fn)(image + u32(functions + u16(ordinals + i * 2) * 4));
    if (!decompress) fail("the library has no OodleLZ_Decompress");
    else if (debug()) fprintf(stderr, "[oodle9] the library is at %p\n", (void *)image);
}

int64_t OodleLZ_Decompress(const void *comp, int64_t comp_size, void *raw, int64_t raw_size, int32_t fuzz_safe, int32_t check_crc,
                           int32_t verbosity, void *dec_base, int64_t dec_size, void *callback, void *callback_data,
                           void *decoder_memory, int64_t decoder_memory_size, int32_t thread_phase) {
    pthread_once(&once, load);
    if (!decompress) return 0;
    unsigned long old = enter();
    int64_t n = decompress(comp, comp_size, raw, raw_size, fuzz_safe, check_crc, verbosity, dec_base, dec_size,
                           callback, callback_data, decoder_memory, decoder_memory_size, thread_phase);
    leave(old);
    return n;
}
