//! C ABI wrapper around `tiger-pkg`.
//!
//! The Python tools (`d2x.pkg`) load this library with `ctypes`. All tag
//! hashes cross the boundary as native `u32` values (`0x80A00123`).

use std::{
    ffi::{c_char, CStr},
    path::{Path, PathBuf},
    ptr, slice,
};

use clap::ValueEnum;
use tiger_pkg::{GameVersion, PackageManager, TagHash};

#[repr(C)]
#[derive(Clone, Copy, Default)]
pub struct TpEntry {
    pub tag: u32,
    pub reference: u32,
    pub file_size: u32,
    pub file_type: u8,
    pub file_subtype: u8,
    pub pkg_id: u16,
}

pub fn parse_version(name: &str) -> anyhow::Result<GameVersion> {
    GameVersion::from_str(name, true).map_err(|e| anyhow::anyhow!("unknown game version: {e}"))
}

/// Opens the packages directory.
///
/// `runtime_dir` must contain `liblinoodle3.so` and `oo2core_3_win64.dll`
/// (pre-Beyond Light), because linoodle resolves the DLL from the working
/// directory when the library is loaded.
pub fn open_manager(
    packages_dir: &Path,
    version: GameVersion,
    runtime_dir: Option<&Path>,
) -> anyhow::Result<PackageManager> {
    let packages_dir = packages_dir.canonicalize()?;
    let previous: Option<PathBuf> = match runtime_dir {
        Some(dir) => {
            let previous = std::env::current_dir()?;
            std::env::set_current_dir(dir)?;
            Some(previous)
        }
        None => None,
    };
    let manager = PackageManager::new(&packages_dir, version, None);
    // Reading one compressed entry forces the Oodle library to load while
    // the working directory still points at the runtime directory.
    if let Ok(manager) = &manager {
        'outer: for (pkg_id, entries) in &manager.lookup.tag32_entries_by_pkg {
            for (index, entry) in entries.iter().enumerate() {
                if entry.file_type == 8 && entry.file_size > 0x40 {
                    let _ = manager.read_tag(TagHash::new(*pkg_id, index as u16));
                    break 'outer;
                }
            }
        }
    }
    if let Some(previous) = previous {
        std::env::set_current_dir(previous)?;
    }
    manager
}

pub fn all_entries(manager: &PackageManager) -> Vec<TpEntry> {
    let mut out = Vec::new();
    for (pkg_id, entries) in &manager.lookup.tag32_entries_by_pkg {
        for (index, entry) in entries.iter().enumerate() {
            out.push(TpEntry {
                tag: TagHash::new(*pkg_id, index as u16).0,
                reference: entry.reference,
                file_size: entry.file_size,
                file_type: entry.file_type,
                file_subtype: entry.file_subtype,
                pkg_id: *pkg_id,
            });
        }
    }
    out.sort_by_key(|e| e.tag);
    out
}

unsafe fn cstr<'a>(value: *const c_char) -> Option<&'a str> {
    if value.is_null() {
        None
    } else {
        CStr::from_ptr(value).to_str().ok()
    }
}

/// # Safety
/// All pointers must be valid NUL-terminated strings or null.
#[no_mangle]
pub unsafe extern "C" fn tp_open(
    packages_dir: *const c_char,
    version: *const c_char,
    runtime_dir: *const c_char,
) -> *mut PackageManager {
    let (Some(dir), Some(version)) = (cstr(packages_dir), cstr(version)) else {
        return ptr::null_mut();
    };
    let runtime = cstr(runtime_dir).map(PathBuf::from);
    let result = parse_version(version)
        .and_then(|v| open_manager(Path::new(dir), v, runtime.as_deref()));
    match result {
        Ok(manager) => Box::into_raw(Box::new(manager)),
        Err(e) => {
            eprintln!("tp_open: {e:#}");
            ptr::null_mut()
        }
    }
}

/// # Safety
/// `manager` must come from `tp_open`.
#[no_mangle]
pub unsafe extern "C" fn tp_close(manager: *mut PackageManager) {
    if !manager.is_null() {
        drop(Box::from_raw(manager));
    }
}

/// # Safety
/// `manager` must come from `tp_open`; `out` must be writable.
#[no_mangle]
pub unsafe extern "C" fn tp_entry(manager: *const PackageManager, tag: u32, out: *mut TpEntry) -> i32 {
    let manager = &*manager;
    let hash = TagHash(tag);
    match manager.get_entry(hash) {
        Some(entry) => {
            *out = TpEntry {
                tag,
                reference: entry.reference,
                file_size: entry.file_size,
                file_type: entry.file_type,
                file_subtype: entry.file_subtype,
                pkg_id: hash.pkg_id(),
            };
            1
        }
        None => 0,
    }
}

/// Returns a buffer that the caller must release with `tp_free`.
///
/// # Safety
/// `manager` must come from `tp_open`; `out_len` must be writable.
#[no_mangle]
pub unsafe extern "C" fn tp_read(manager: *const PackageManager, tag: u32, out_len: *mut u64) -> *mut u8 {
    let manager = &*manager;
    match manager.read_tag(TagHash(tag)) {
        Ok(data) => {
            let mut boxed = data.into_boxed_slice();
            *out_len = boxed.len() as u64;
            let pointer = boxed.as_mut_ptr();
            std::mem::forget(boxed);
            pointer
        }
        Err(_) => {
            *out_len = 0;
            ptr::null_mut()
        }
    }
}

/// # Safety
/// `data`/`len` must come from `tp_read`.
#[no_mangle]
pub unsafe extern "C" fn tp_free(data: *mut u8, len: u64) {
    if !data.is_null() {
        drop(Box::from_raw(slice::from_raw_parts_mut(data, len as usize)));
    }
}

/// Returns every entry of every package. Release with `tp_free_list`.
///
/// # Safety
/// `manager` must come from `tp_open`; `out_count` must be writable.
#[no_mangle]
pub unsafe extern "C" fn tp_list(manager: *const PackageManager, out_count: *mut u64) -> *mut TpEntry {
    let mut boxed = all_entries(&*manager).into_boxed_slice();
    *out_count = boxed.len() as u64;
    let pointer = boxed.as_mut_ptr();
    std::mem::forget(boxed);
    pointer
}

/// # Safety
/// `data`/`count` must come from `tp_list`.
#[no_mangle]
pub unsafe extern "C" fn tp_free_list(data: *mut TpEntry, count: u64) {
    if !data.is_null() {
        drop(Box::from_raw(slice::from_raw_parts_mut(data, count as usize)));
    }
}

/// Writes the package file name into `buffer`. Returns the name length, or -1.
///
/// # Safety
/// `manager` must come from `tp_open`; `buffer` must hold `capacity` bytes.
#[no_mangle]
pub unsafe extern "C" fn tp_pkg_name(
    manager: *const PackageManager,
    pkg_id: u16,
    buffer: *mut u8,
    capacity: u64,
) -> i32 {
    let manager = &*manager;
    let Some(path) = manager.package_paths.get(&pkg_id) else {
        return -1;
    };
    let name = path.filename.as_bytes();
    let count = name.len().min(capacity as usize);
    ptr::copy_nonoverlapping(name.as_ptr(), buffer, count);
    count as i32
}
