# Basic Assembler
This is a simple program to generate IPS patches based on Arm64 assembly language for binary game patches.

## Setup and Running
To run, you will need
- The [Keystone assembler framework](https://www.keystone-engine.org/)
- [Rust and Cargo](https://rustup.rs/)

After both are installed (make sure you run `make install` on Keystone), its as simple as running `cargo run -- input.s output.ips` to generate the ips file.

## Patch Spec and Information
The format is as follows:
```
;; This is a 3 instruction patch that will be inserted
;; at 0x13cc8c in the program.
0x13cc8c
mov w12, #0x10
mul x12, x12, x10
ucvtf s5, x12
end

;; This is a 2 instruction patch that will be
;; inserted at 0x1433f0 in the program
0x1433f0
nop
mov w10, #0x10
end
```

### Extensions
There are some assembler extensions just to make some common tasks easier.:

#### `call`
The call instruction is an alias to `bl` that automatically calculates relative offsets for an absolute address.

**All absolute instructions must be prefixed with the immediate indicating # character**.

Usage is simple:
```assembly
0x1433f0
mov w12, #0x10
call #0x1433B4
end
```

Will be translated into:
```asssembly
mov w12, #0x10
bl #-0xC3C
```

### IPS Patches
IPS patches must be named with the switch ID of the game the patch is being applied to.

For more info, see the [IPS spec](https://zerosoft.zophar.net/ips.php) and the [Yuzu modding page](https://yuzu-emu.org/help/feature/game-modding/).