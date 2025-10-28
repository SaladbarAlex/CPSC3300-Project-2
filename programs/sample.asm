# Demo program:
# t0 = 0
# t0 = t0 + 42
# store t0 to mem[0x100]
# zero t1, load it back into t1, compare equal, if equal skip addi
# jump to label end, then halt

    addi $t0, $zero, 0       # t0 = 0
    addi $t0, $t0, 42        # t0 = t0 + 42
    sw   $t0, 0x100($zero)   # MEM[0x100] = t0
    lw   $t1, 0x100($zero)   # t1 = MEM[0x100]
    beq  $t0, $t1, same      # if equal, branch
    addi $t0, $t0, 1         # not taken path
same:
    j    end
    add  $t2, $t0, $t1       # (delay slot is *not* modeled; still executes as normal next PC+4)
end:
    halt
