| ---------------------------------------------------------------------------
| Raiden (World) Atari Jaguar -- trainer menu, autofire and cheat hooks.
| GNU as (m68k-linux-gnu-as -m68000 --register-prefix-optional), linked at
| $801000 (ROM file offset $1000, spare space in the universal header; the
| ROM stays 2 MB).
|
| The boot stub (copied to $180000) unpacks RAIDEN.DTA/RAIDEN.TXT to RAM
| $3000 and ends with  st.b $2c6(a4) / jmp $3000.w  at $180112.  build.py
| turns that into  jmp TrainerEntry.l / nop, so the menu runs once the game
| code is in RAM.  On exit the menu writes the chosen hooks into the game
| code in RAM and jumps to $3000, which starts the game exactly as before.
| ---------------------------------------------------------------------------
        .include "build/config.inc"

| ---- game addresses (RAM, after unpacking) --------------------------------
        .equ STUB_A4,      0x1803b2     | stub's variable base
        .equ STUB_STOPOLP, 0x18067a     | stub routine: OLP -> its stop object
        .equ GAME_START,   0x3000
        .equ READPADS,     0x19930      | game's joypad reader
        .equ PAD1_HELD,    0x58a14
        .equ PAD2_HELD,    0x58a18
        .equ PAD1_PRESS,   0x58a0c
        .equ P1,           0x57b34      | player 1 struct (a3)
        .equ DEMO,         0x3486       | (a4): attract demo playing

        .equ H_LIVES,      0x240ee      | tst.w $19ce8.l / bne: skip lives -1
        .equ H_BOMBS,      0x2307c      | tst.w $19ce8.l / bne: skip bombs -1
        .equ DEVFLAG,      0x19ce8      | game's own debug "infinite" flag
        .equ H_INVULN,     0x1fb12      | tst.b $745(a3) / beq.b  (6 bytes)
        .equ H_INVULN_HIT, 0x1fb1c      | "hit" path of the player collision
        .equ H_STAGE,      0x22b6e      | move.b #1,$3442(a4)     (6 bytes)
        .equ H_FIRE1,      0x23a66      | jsr $19a22.l (P1 fire A held)
        .equ H_FIREB1,     0x23a70      | jsr $19a2e.l / beq / st (P1 fire B)
        .equ H_FIRE2,      0x23b24      | jsr $19a6e.l (P2 fire A held)
        .equ H_FIREB2,     0x23b2e      | jsr $19a7a.l / beq / st (P2 fire B)
        .equ H_HISCORE,    0x188aa      | bmi.w $189cc: not in the table

| ---- hardware ---------------------------------------------------------------
        .equ OLP,     0xf00020
        .equ VMODE,   0xf00028
        .equ BG,      0xf00058
        .equ INT1,    0xf000e0
        .equ INT2,    0xf000e2
        .equ CLUT,    0xf00400
        .equ VEC_INT, 0x100

| ---- our RAM ----------------------------------------------------------------
| $2F00-$2FFF is never touched by the game (checked over attract, all stages,
| game over and name entry by test/ramcheck.py).
        .equ VARS,     0x2f00
        .equ OPTS,     VARS+0x00    | one byte per menu line (see Items)
        .equ AFCNT,    VARS+0x10    | autofire counters, P1 / P2
        .equ VBLFLAG,  VARS+0x12
        .equ CURSOR,   VARS+0x13
        .equ OLDVEC,   VARS+0x14
        .equ OLDSR,    VARS+0x18
        .equ OPT_LIVES,  OPTS+0
        .equ OPT_BOMBS,  OPTS+1
        .equ OPT_INVULN, OPTS+2
        .equ OPT_POWER,  OPTS+3
        .equ OPT_STAGE,  OPTS+4
        .equ OPT_AUTO,   OPTS+5
        .equ NITEMS,     6

| menu-only RAM (the game clears and reuses it after the menu)
        .equ OBJLIST, 0x0f0000      | object list, 16-byte aligned
        .equ FB,      0x100000      | 320x240 8 bpp frame buffer
        .equ FBW,     320
        .equ FBH,     240

| ---- colours (CLUT index; RGB16 = R5 B5 G6) ------------------------------------
        .equ C_BG,    0
        .equ C_WHITE, 1
        .equ C_YELLOW,2
        .equ C_GREEN, 3
        .equ C_BLUE,  4

| ---- pad bits (game's layout) ------------------------------------------------
        .equ B_UP,20
        .equ B_DOWN,21
        .equ B_LEFT,22
        .equ B_RIGHT,23
        .equ B_A,29
        .equ B_B,25
        .equ B_C,13
        .equ B_PAUSE,28
        .equ B_OPTION,9

| ---- layout (8x8 cells, 40x30) ------------------------------------------------
        .equ CURSOR_COL, 5
        .equ NAME_COL,   7
        .equ STATE_COL,  30

        .text
        .globl TrainerEntry
| ===========================================================================
TrainerEntry:
        move.w  sr,(OLDSR).l
        lea     STUB_A4,a4
        st.b    0x2c6(a4)               | what the stub did before jmp $3000
        move.w  #0x2700,sr

        | defaults
        lea     (VARS).l,a0
        moveq   #0x3f,d0
1:      clr.l   (a0)+
        dbra    d0,1b
        move.b  #DEF_AUTOFIRE,(OPT_AUTO).l
        .if NOMENU
        move.b  #1,(OPT_AUTO).l         | autofire-only build: no menu
        bsr     InstallHooks
        move.w  (OLDSR).l,sr
        jmp     (GAME_START).w
        .endif

        | frame buffer: clear to background
        lea     (FB).l,a0
        move.w  #(FBW*FBH/16)-1,d0
        moveq   #0,d1
2:      move.l  d1,(a0)+
        move.l  d1,(a0)+
        move.l  d1,(a0)+
        move.l  d1,(a0)+
        dbra    d0,2b

        bsr     DrawStatic
        bsr     DrawItems

        | palette (RGB16 mode while the menu is up)
        lea     Palette(pc),a0
        lea     (CLUT).l,a1
        moveq   #4,d0
3:      move.w  (a0)+,(a1)+
        dbra    d0,3b
        move.w  Palette(pc),(BG).l

        bsr     BuildList
        move.l  (VEC_INT).w,(OLDVEC).l
        move.l  #MenuVbl,(VEC_INT).w
        move.w  #0x6c7,(VMODE).l        | stub mode $6C1 with RGB16
        move.w  #0x101,(INT1).l
        move.w  #0,(INT2).l
        move.w  #0x2100,sr

        | wait for all buttons up so the button that skipped the logo
        | does not change a setting
MenuWaitUp:
        bsr     WaitVbl
        jsr     READPADS
        tst.l   (PAD1_HELD).l
        bne.s   MenuWaitUp

MenuLoop:
        bsr     WaitVbl
        jsr     READPADS
        move.l  (PAD1_PRESS).l,d0
        btst    #B_PAUSE,d0
        bne     MenuExit
        btst    #B_OPTION,d0
        bne     MenuExit
        moveq   #0,d1
        move.b  (CURSOR).l,d1
        btst    #B_UP,d0
        beq.s   1f
        subq.b  #1,d1
        bpl.s   9f
        moveq   #NITEMS-1,d1
        bra.s   9f
1:      btst    #B_DOWN,d0
        beq.s   2f
        addq.b  #1,d1
        cmpi.b  #NITEMS,d1
        bne.s   9f
        moveq   #0,d1
        bra.s   9f
2:      | change setting: A/B/C/RIGHT next, LEFT previous
        lea     (OPTS).l,a0
        lea     Kinds(pc),a1
        moveq   #0,d2
        move.b  (a1,d1.w),d2            | number of values (2 = OFF/ON)
        move.l  d0,d3
        andi.l  #(1<<B_A)+(1<<B_B)+(1<<B_C)+(1<<B_RIGHT),d3
        beq.s   3f
        addq.b  #1,(a0,d1.w)
        cmp.b   (a0,d1.w),d2
        bne.s   9f
        clr.b   (a0,d1.w)
        bra.s   9f
3:      btst    #B_LEFT,d0
        beq.s   MenuLoop
        subq.b  #1,(a0,d1.w)
        bpl.s   9f
        subq.b  #1,d2
        move.b  d2,(a0,d1.w)
9:      move.b  d1,(CURSOR).l
        bsr     DrawItems
        bra     MenuLoop

| ---------------------------------------------------------------------------
MenuExit:
        bsr     WaitVbl
        move.w  #0x2700,sr
        move.l  (OLDVEC).l,(VEC_INT).w
        move.w  #0x6c1,(VMODE).l
        move.w  #0,(BG).l
        lea     (CLUT).l,a0             | stub left the CLUT black (faded)
        move.w  #255,d0
1:      clr.w   (a0)+
        dbra    d0,1b
        lea     STUB_A4,a4
        jsr     STUB_STOPOLP            | what the stub's VBL does now
        lea     (PAD1_PRESS).l,a0       | no stale pad state for the game
        moveq   #3,d0
2:      clr.l   (a0)+
        dbra    d0,2b
        clr.w   (AFCNT).l

        bsr     InstallHooks
        move.w  (OLDSR).l,sr
        jmp     (GAME_START).w

| ---------------------------------------------------------------------------
| Write the hooks for the chosen options into the game code in RAM.
InstallHooks:
        moveq   #0,d7                   | d7 = any cheat on
        tst.b   (OPT_LIVES).l
        beq.s   1f
        lea     (H_LIVES).l,a0
        move.w  #0x4eb9,(a0)+
        move.l  #KeepHook,(a0)
        st      d7
1:      tst.b   (OPT_BOMBS).l
        beq.s   2f
        lea     (H_BOMBS).l,a0
        move.w  #0x4eb9,(a0)+
        move.l  #KeepHook,(a0)
        st      d7
2:      tst.b   (OPT_INVULN).l
        beq.s   3f
        lea     (H_INVULN).l,a0
        move.w  #0x4eb9,(a0)+
        move.l  #InvulnHook,(a0)
        st      d7
3:      tst.b   (OPT_STAGE).l
        beq.s   4f
        lea     (H_STAGE).l,a0
        move.w  #0x4eb9,(a0)+
        move.l  #StageHook,(a0)
        st      d7
4:      tst.b   (OPT_POWER).l
        beq.s   5f
        st      d7
5:      move.b  (OPT_POWER).l,d0
        or.b    (OPT_AUTO).l,d0
        beq.s   6f
        lea     (H_FIRE1).l,a0          | P1: A/B -> FireHook, skip B test
        move.w  #0x4eb9,(a0)+
        move.l  #FireHook,(a0)
        move.w  #0x600a,(H_FIREB1).l    | bra.s past jsr/beq/st
        lea     (H_FIRE2).l,a0          | P2 the same
        move.w  #0x4eb9,(a0)+
        move.l  #FireHook,(a0)
        move.w  #0x600a,(H_FIREB2).l
6:      tst.b   d7
        beq.s   7f
        move.w  #0x6000,(H_HISCORE).l   | bmi.w -> bra.w: never enter the table
7:      rts

ConstOn: .word 0xffff

| ---------------------------------------------------------------------------
| In-game hooks.  a3 = player struct, a4 = game globals.

| Replaces "tst.w $19ce8.l" before the lives and bombs decrements: Z clear
| (keep the count) in a real game, the game's own test in the attract demo.
KeepHook:
        tst.b   DEMO(a4)
        bne.s   1f
        tst.w   (ConstOn).l
        rts
1:      tst.w   (DEVFLAG).l
        rts

| Replaces "tst.b $745(a3) / beq.b hit" in the player collision: returning
| normally lands on the game's own "still blinking after a respawn, ignore
| the hit" path, which is what the cheat wants outside the attract demo.
InvulnHook:
        tst.b   DEMO(a4)
        bne.s   1f
        rts
1:      tst.b   0x745(a3)
        bne.s   2f
        move.l  #H_INVULN_HIT,(sp)
2:      rts

| Replaces "move.b #1,$3442(a4)" in the new game set-up.
StageHook:
        move.b  #1,0x3442(a4)
        tst.b   DEMO(a4)
        bne.s   1f
        move.l  d0,-(sp)
        move.b  (OPT_STAGE).l,d0
        addq.b  #1,d0
        move.b  d0,0x3442(a4)
        move.l  (sp)+,d0
1:      rts

| Replaces "jsr $19a22.l" (P1) / "jsr $19a6e.l" (P2): returns Z clear when
| the player shoots this frame.  Only d0 may change, as in the original.
FireHook:
        move.l  a0,-(sp)
        lea     (AFCNT).l,a0
        move.l  (PAD1_HELD).l,d0
        cmpa.l  #P1,a3
        beq.s   1f
        addq.l  #1,a0
        move.l  (PAD2_HELD).l,d0
1:      tst.b   (OPT_POWER).l
        beq.s   2f
        move.b  #7,0x74c(a3)            | main shot at full power
        cmpi.b  #-1,0x74d(a3)           | missiles at full power once held
        beq.s   2f
        move.b  #4,0x74e(a3)
2:      andi.l  #(1<<B_A)+(1<<B_B),d0
        beq.s   NoFire
        tst.b   (OPT_AUTO).l
        beq.s   Fire
        addq.b  #1,(a0)
        move.b  (a0),d0
        cmpi.b  #2,(OPT_AUTO).l
        beq.s   10f
        andi.b  #2,d0                   | ON: 2 game frames pressed, 2 released,
        seq     d0                      | as fast as the game's cooldown allows
        bra.s   FireOut
10:     clr.b   0x748(a3)               | TURBO: skip the game's shot cooldown
        andi.b  #1,d0                   | and press every other game frame
        seq     d0                      | (more bullets than the game expects)
        bra.s   FireOut
NoFire: clr.b   (a0)
        moveq   #0,d0
        bra.s   FireOut
Fire:   moveq   #1,d0
FireOut:
        tst.b   d0
        movea.l (sp)+,a0                | movea keeps the flags
        rts

| ---------------------------------------------------------------------------
MenuVbl:
        movem.l d0/a0-a1,-(sp)
        bsr     BuildList
        st.b    (VBLFLAG).l
        move.w  #0x101,(INT1).l
        move.w  #0,(INT2).l
        movem.l (sp)+,d0/a0-a1
        rte

| The object processor writes back into the list, so rebuild it every frame.
BuildList:
        lea     ListTemplate(pc),a0
        lea     (OBJLIST).l,a1
        moveq   #5,d0
1:      move.l  (a0)+,(a1)+
        dbra    d0,1b
        move.l  #OBJLIST,d0
        swap    d0
        move.l  d0,(OLP).l
        rts

WaitVbl:
        clr.b   (VBLFLAG).l
1:      tst.b   (VBLFLAG).l
        beq.s   1b
        rts

| ---------------------------------------------------------------------------
| Text.  DrawStr: a0 = string (0-terminated), d0 = column, d1 = row,
| d2 = colour.  DrawCentred: same, column computed.
DrawCentred:
        movea.l a0,a1
        moveq   #-1,d0
1:      addq.w  #1,d0
        tst.b   (a1)+
        bne.s   1b
        neg.w   d0
        addi.w  #40,d0
        lsr.w   #1,d0
DrawStr:
        movem.l d0-d6/a0-a2,-(sp)
1:      moveq   #0,d3
        move.b  (a0)+,d3
        beq.s   9f
        bsr.s   DrawChar
        addq.w  #1,d0
        bra.s   1b
9:      movem.l (sp)+,d0-d6/a0-a2
        rts

| d3 = char, d0 = column, d1 = row, d2 = colour
DrawChar:
        movem.l d0-d6/a1-a2,-(sp)
        subi.w  #0x20,d3
        bpl.s   1f
        moveq   #0,d3
1:      lsl.w   #3,d3
        lea     Font(pc),a2
        adda.w  d3,a2
        lea     (FB).l,a1
        lsl.w   #3,d0
        adda.w  d0,a1
        mulu.w  #FBW*8,d1
        adda.l  d1,a1
        moveq   #7,d4
2:      move.b  (a2)+,d5
        moveq   #7,d6
3:      add.b   d5,d5
        bcc.s   4f
        move.b  d2,(a1)+
        bra.s   5f
4:      clr.b   (a1)+
5:      dbra    d6,3b
        lea     FBW-8(a1),a1
        dbra    d4,2b
        movem.l (sp)+,d0-d6/a1-a2
        rts

DrawStatic:
        lea     StrTitle(pc),a0
        moveq   #2,d1
        moveq   #C_BLUE,d2
        bsr     DrawCentred
        lea     StrRule(pc),a0
        moveq   #4,d1
        bsr     DrawCentred
        lea     StrOptions(pc),a0
        moveq   #ROW_OPTHDR,d1
        bsr     DrawCentred
        lea     StrRule(pc),a0
        moveq   #23,d1
        bsr     DrawCentred
        moveq   #C_WHITE,d2
        moveq   #24,d1
        lea     StrHelp1(pc),a0
        bsr     DrawCentred
        moveq   #25,d1
        lea     StrHelp2(pc),a0
        bsr     DrawCentred
        moveq   #26,d1
        lea     StrHelp3(pc),a0
        bsr     DrawCentred
        rts

| Redraw every menu line (cursor, name, value).
DrawItems:
        movem.l d0-d7/a0-a3,-(sp)
        moveq   #0,d7                   | item index
1:      moveq   #0,d1
        lea     Rows(pc),a0
        move.b  (a0,d7.w),d1            | row
        moveq   #C_WHITE,d2
        cmp.b   (CURSOR).l,d7
        bne.s   2f
        moveq   #C_YELLOW,d2
2:      | cursor
        moveq   #CURSOR_COL,d0
        moveq   #' ',d3
        cmpi.b  #C_YELLOW,d2
        bne.s   3f
        moveq   #'>',d3
3:      bsr     DrawChar
        | name
        lea     Names(pc),a0
        move.w  d7,d3
        add.w   d3,d3
        move.w  (a0,d3.w),d3
        lea     (a0,d3.w),a0
        moveq   #NAME_COL,d0
        bsr     DrawStr
        | value: kind 2 = OFF/ON, otherwise 1..n
        lea     (OPTS).l,a1
        moveq   #0,d4
        move.b  (a1,d7.w),d4
        lea     Kinds(pc),a1
        cmpi.b  #3,(a1,d7.w)            | kind 3 = OFF/ON/TURBO
        bne.s   31f
        lea     StrAuto(pc),a0
        move.w  d4,d3
        mulu.w  #6,d3
        adda.w  d3,a0
        tst.b   d4
        beq.s   4f
        bra.s   32f
31:     cmpi.b  #2,(a1,d7.w)
        bne.s   5f
        lea     StrOff(pc),a0
        tst.b   d4
        beq.s   4f
        lea     StrOn(pc),a0
32:
        cmpi.b  #C_YELLOW,d2
        beq.s   4f
        moveq   #C_GREEN,d2
4:      moveq   #STATE_COL,d0
        bsr     DrawStr
        bra.s   6f
5:      cmpi.b  #C_YELLOW,d2
        beq.s   51f
        moveq   #C_GREEN,d2
51:     moveq   #STATE_COL,d0
        moveq   #' ',d3
        bsr     DrawChar
        addq.w  #1,d0
        bsr     DrawChar
        addq.w  #1,d0
        moveq   #'1',d3
        add.w   d4,d3
        bsr     DrawChar
6:      addq.w  #1,d7
        cmpi.w  #NITEMS,d7
        bne     1b
        movem.l (sp)+,d0-d7/a0-a3
        rts

| ---------------------------------------------------------------------------
        .equ ROW_OPTHDR, 17
Rows:   .byte 7,9,11,13,15,19
Kinds:  .byte 2,2,2,2,8,3
        .even
Names:  .word N0-Names,N1-Names,N2-Names,N3-Names,N4-Names,N5-Names
N0:     .asciz "INFINITE LIVES"
N1:     .asciz "INFINITE BOMBS"
N2:     .asciz "INVULNERABLE"
N3:     .asciz "MAX POWER"
N4:     .asciz "START STAGE"
N5:     .asciz "AUTOFIRE"
StrOn:  .asciz "ON "
StrOff: .asciz "OFF"
StrAuto: .asciz "OFF  "
        .asciz "ON   "
        .asciz "TURBO"
StrTitle:   .asciz TITLE
StrRule:    .asciz "--------------------------------"
StrOptions: .asciz "-------- GAME OPTIONS --------"
StrHelp1:   .asciz "UP/DOWN        CHOOSE CHEAT  "
StrHelp2:   .asciz "A/B/C/LEFT     CHANGE SETTING"
StrHelp3:   .asciz "PAUSE/OPTION   BEGIN GAME    "
        .even
Palette:    | RGB16: RRRRRBBBBBGGGGGG
        .word (0<<11)+(10<<6)+0          | 0 dark blue background
        .word (31<<11)+(31<<6)+63        | 1 white
        .word (31<<11)+(0<<6)+63         | 2 yellow
        .word (0<<11)+(0<<6)+63          | 3 green
        .word (10<<11)+(31<<6)+41        | 4 light blue (title)

        .balign 8
ListTemplate:                           | built by build.py: bitmap + stop
        .include "build/objlist.inc"

Font:   .include "build/font.inc"
