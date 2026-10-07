//! `tigerx`: list and unpack Tiger engine package entries.

use std::{fs, io::Write, path::PathBuf};

use clap::{Parser, Subcommand};
use tiger_pkg::TagHash;
use tigerpkg_ffi::{all_entries, open_manager, parse_version};

#[derive(Parser)]
#[command(about = "List and unpack Tiger engine package entries")]
struct Args {
    /// Path to the game `packages` directory
    #[arg(short, long)]
    packages: PathBuf,
    /// Game version code (d2_sk, d2_bl, d2_wq, ...)
    #[arg(short, long, default_value = "d2_sk")]
    version: String,
    /// Directory with liblinoodle3.so and oo2core_3_win64.dll
    #[arg(short, long)]
    runtime: Option<PathBuf>,
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Print all entries as TSV: tag, reference, type, subtype, size, package
    List,
    /// Write the given tags (hex, for example 80A00123) to a directory
    Get {
        /// Output directory (no default: the tool does not write into the working directory)
        #[arg(short, long)]
        output: PathBuf,
        tags: Vec<String>,
    },
    /// Write all entries of one type (and optional subtype) to a directory
    Dump {
        /// Output directory (no default: the tool does not write into the working directory)
        #[arg(short, long)]
        output: PathBuf,
        #[arg(long = "type")]
        file_type: u8,
        #[arg(long)]
        subtype: Option<u8>,
        /// Only entries whose reference (class) has this hex value
        #[arg(long)]
        reference: Option<String>,
    },
}

fn main() -> anyhow::Result<()> {
    let args = Args::parse();
    let version = parse_version(&args.version)?;
    let manager = open_manager(&args.packages, version, args.runtime.as_deref())?;
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());

    match args.command {
        Command::List => {
            for e in all_entries(&manager) {
                let name = manager
                    .package_paths
                    .get(&e.pkg_id)
                    .map(|p| p.filename.as_str())
                    .unwrap_or("?");
                writeln!(
                    out,
                    "{:08X}\t{:08X}\t{}\t{}\t{}\t{}",
                    e.tag, e.reference, e.file_type, e.file_subtype, e.file_size, name
                )?;
            }
        }
        Command::Get { output, tags } => {
            fs::create_dir_all(&output)?;
            for text in tags {
                let tag = TagHash(u32::from_str_radix(text.trim_start_matches("0x"), 16)?);
                match manager.read_tag(tag) {
                    Ok(data) => {
                        fs::write(output.join(format!("{:08X}.bin", tag.0)), data)?;
                        writeln!(out, "{:08X}\tok", tag.0)?;
                    }
                    Err(e) => writeln!(out, "{:08X}\terror: {e}", tag.0)?,
                }
            }
        }
        Command::Dump { output, file_type, subtype, reference } => {
            fs::create_dir_all(&output)?;
            let reference = match reference {
                Some(text) => Some(u32::from_str_radix(text.trim_start_matches("0x"), 16)?),
                None => None,
            };
            let mut count = 0usize;
            for e in all_entries(&manager) {
                if e.file_type != file_type
                    || subtype.is_some_and(|s| s != e.file_subtype)
                    || reference.is_some_and(|r| r != e.reference)
                {
                    continue;
                }
                if let Ok(data) = manager.read_tag(TagHash(e.tag)) {
                    fs::write(output.join(format!("{:08X}.bin", e.tag)), data)?;
                    count += 1;
                }
            }
            writeln!(out, "wrote {count} entries")?;
        }
    }
    Ok(())
}
