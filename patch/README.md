# Writing patches

`patchlist.xml` lists byte patches for the main executable of a game. Vita3K writes the bytes into the loaded module right after it is loaded, before the game starts to run.

## Entry format

```xml
<!-- Hatsune Miku: Project Diva X -->
<TitleID>
	<ID>PCSG00683</ID>
</TitleID>
<Metadata Title="Hatsune Miku: Project Diva X"
					Name="Skip intro"
					Author=""
					Note=""
					PatchVer="1.0"
					AppVer="1.00"
					AppElf="eboot.bin"
					NID="0xCAF82C1B">
	<PatchList>
		<Line Type="bytes" Address="0x1175C0" Value="0020"/>
		<Line Type="bytes" Address="0x1B6D60" Value="2EE0"/>
	</PatchList>
</Metadata>
```

- `<TitleID>` lists the serials the following `<Metadata>` elements apply to. Several `<Metadata>` can follow one `<TitleID>` (60FPS and Skip intro of the same game, for example).
- `Title`, `Name`, `Author`, `Note`, `PatchVer` are shown in the Patch Manager. A patch is identified by serial, `AppVer`, `AppElf`, `NID` and `Name`, so changing `Name` makes it a different patch.
- `AppVer` is the game version. Leave it empty to match any version. `1.02` and `01.02` are equal.
- `AppElf` is the executable the patch is for (default `eboot.bin`).
- `NID` is the NID of the main executable and is **required**. A patch with an empty `NID` is never applied. Vita3K prints it when the game starts: `Main executable NID: 0x... (for the NID attribute of a patch)`.
- Patches for different versions or regions of a game need separate `<TitleID>` and `<Metadata>` blocks, because the offsets differ.

### Lines

Only `Type="bytes"` is supported.

- `Address` is `<offset>` in segment 0, or `<segment>:<offset>` (hexadecimal). The offset is relative to the start of that segment in memory, and the patch must fit in the segment. Code is normally in segment 0 and writable data in segment 1.
- `Value` is a list of bytes in memory order, with or without `0x` and spaces: `2EE0`, `0x2E 0xE0`. Instructions are stored as little-endian halfwords, so Thumb `movs r0, #1` (`0x2001`) is `0120`, and the 4 byte `vmov.f32 s1, #0.5` (`0xEEF6 0x0A00`) is `F6EE000A`.
- `t1_mov(rd, imm)` can be used instead of bytes and produces a Thumb `movs rd, #imm`: `t1_mov(0, 1)` is `0120`.

## Finding what to patch

1. **Get the serial, version and NID.** Start the game once and read the log (`Serial`, `Version`, `Main executable NID`).
2. **Get the code.** Turn on **Settings > Debug > ELF Dumping** (it is not saved, so it has to be turned on every time), start the game, and take `<start>-<end>_eboot.elf` from the `elfdumps/<serial>` folder next to `vita3k.log`. The dump is the memory image of the module. The log line `Loaded module segment 0 @ [...]` tells the load address of each segment. Patch offset = address in the game - load address of the segment (for most games segment 0 is at `0x81000000`, so `0x811175C0` is offset `0x1175C0`).
3. **Disassemble it.** Ghidra works, and so does any ARM Thumb-2 disassembler, for example Capstone (`Cs(CS_ARCH_ARM, CS_MODE_THUMB)`). Most game code is Thumb-2, so use a 2 byte aligned address.
4. **Find the code by its strings.** Search the dump for file names or names the game uses (`.avc`, `logo`, `movie`, `opening`, ...), then search the code for references to them. Newer compilers load an address with a `movw`/`movt` pair, older ones with a literal pool word. Functions that use a string tell you which function handles it.
5. **Change as little as possible.** Replace one instruction, a constant, or the start of a function, and keep the instruction size. Verify the new bytes by disassembling them at the target address before testing.

Useful edits:

| Goal | Bytes (Thumb) |
| --- | --- |
| Return `true` at once | `0120 7047` (`movs r0, #1` + `bx lr`) at the start of the function |
| Return `false` at once | `0020 7047` |
| Make `cmp r0, #0` set Z (treat a result as 0) | `0020` (`movs r0, #0`) over the `cmp` |
| Never take / always take a conditional branch | `00BF` (nop) over a 2 byte branch / `b` to the same target |
| Replace a call returning a flag with a constant | `0120 00BF` (`movs r0, #1` + nop) over a 4 byte `bl` |
| Change a constant | edit the `movs`/`movw`/`movt` operand, or the value in the data segment (`1:<offset>`) |

An unconditional `b.n` is `E000 | (distance / 2)` where distance = target - (address + 4), for distances up to about 2 KB. Use a disassembler to check the target.

## Testing

1. Enable the patch in the Patch Manager (or use a [personal patch file](#legacy-txt-format)).
2. Start the game and check the log: `Enabled patch: ...` and `Patching segment ... at offset ... with N values`. `Patch out of bounds` means the offset is wrong.
3. Test on a copy of the Vita3K folder if you can, and test the whole flow you changed (title screen, pressing a button, ...), not only the first screen.
4. If the game hangs on a black screen, the patch skipped something the game waits for. Patch a smaller part of the flow.

## Submitting

- Keep the entries in the style of the existing ones (tab indented, one `<Line>` per patch, `Name="Skip intro"` or `Name="60FPS"`) and put the game's name in a comment above its `<TitleID>`.
- Fill in `AppVer` and `NID`, and test every version you add separately.
- Use LF line endings.
