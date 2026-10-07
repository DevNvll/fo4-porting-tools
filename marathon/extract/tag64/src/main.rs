//! `tag64 PACKAGES VERSION`: one line for each 64-bit tag hash of the packages:
//! the 64-bit hash, the 32-bit tag and the class (reference), in hexadecimal, with tabs.
//! The table is in the header of each package, so no entry is decoded and no Oodle library is necessary.

use std::io::Write;

use clap::ValueEnum;
use tiger_pkg::{GameVersion, PackageManager};

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        anyhow::bail!("usage: tag64 PACKAGES VERSION");
    }
    let version = GameVersion::from_str(&args[2], true).map_err(|e| anyhow::anyhow!("unknown game version: {e}"))?;
    let manager = PackageManager::new(std::path::Path::new(&args[1]).canonicalize()?, version, None)?;
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    for (hash64, entry) in &manager.lookup.tag64_entries {
        writeln!(out, "{:016X}\t{:08X}\t{:08X}", hash64, entry.hash32.0, entry.reference.0)?;
    }
    Ok(())
}
