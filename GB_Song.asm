
vasm equ 1
BuildGMB equ 1 ; Build for GameBoy Regular

	include ".\ResourceFIles\VasmBuildCompat.asm"
	include ".\ResourceFIles\GB_V1_Header.asm"
	
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
;			Program start
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

	Call DOINIT
	call Cls	

	ld a,%01110111 ;-LLL-RRR Channel volume

	;Turn all sound channels on. 
	ld a,%11111111 ;Mixer LLLLRRRR Channel 1-4 L / Chanel 1-4R
	ld (&FF25),a
		
	ld hl,SongBytes
	call PlaySong
	
	di
	halt

;;;;;

Tones:
ToneC: db 0,11		
ToneCs: db 0,40
ToneD: db 0,66
ToneDs: db 0,91
ToneE: db 0,114	
ToneF: db 0,137
ToneFs: db 0,158
ToneG: db 0,177
ToneGs: db 0,196
ToneA: db 0,214
ToneAs: db 0,231
ToneB: db 0,246
ToneC2: db 1,5
ToneCs2: db 1,20
ToneD2: db 1,33
ToneDs2: db 1,46
ToneE2: db 1,58
ToneF2: db 1,69
ToneFs2: db 1,79
ToneG2: db 1,89
ToneGs2: db 1,98
ToneA2: db 1,107
ToneAs2: db 1,116
ToneB2: db 1,123
ToneC3: db 1,131
ToneCs3: db 1,138
ToneD3: db 1,144
ToneDs3: db 1,151
ToneE3: db 1,157
ToneF3: db 1,163
ToneFs3: db 1,167
ToneG3: db 1,172
ToneGs3: db 1,177
ToneA3: db 1,181
ToneAs3: db 1,186
ToneB3: db 1,190
ToneC4: db 1,193
ToneCs4: db 1,197
ToneD4: db 1,200


PlaySong:
	NextTone:
	ldi a,(hl)	;check end
	cp 255
	jr z,DoneSong
	
	ldd a,(hl)
	cp 0
	jr z,PlayOnSecondChannel

	call PlayNoteOnChannel1
	call Spin
	jr DoneNote
	
	PlayOnSecondChannel:
	call PlayNoteOnChannel2
	jr DoneNote

	DoneNote:
	inc hl
	inc hl
	jr NextTone
	
	DoneSong:
	ret
	
PlayNoteOnChannel1:
	push hl
	ldi a,(hl)	;note
	ld d,(hl)	;delay
	ld hl,Tones	;ToneC
	
	ld b,0
	ld c,a		;note
	add hl,bc
	add hl,bc	;note offset
	

	ld b,(hl)
	inc hl
	ld c,(hl)
	
	
	pop hl
	call BeepChannel1
	ret
	
PlayNoteOnChannel2:
	push hl
	ldi a,(hl)	;note
	ld d,(hl)	;delay
	ld hl,Tones	;ToneC
	
	ld b,0
	ld c,a		;note
	add hl,bc
	add hl,bc	;note offset
	

	ld b,(hl)
	inc hl
	ld c,(hl)
	
	
	pop hl
	call BeepChannel2
	ret
	
SongBytes:
	include ".\Song_Bytes.asm"


BeepChannel2:
	;ret
	; ;this is a shift in pitch over time, rather than volume
	ld a,%00000111	;Channel 1 Sweep register (R/W)
	ld (&FF10),a	;-TTTDNNN	T=Time,D=direction,N=Numberof shifts 

	ld a,%11011111
	ld (&FF11),a	;Sound Length

	ld a,%11110000	;%VVVVDNNN C1 Volume / Direction 0=down / envelope Number (fade speed)
	ld (&FF12),a

	ld a,c			;%LLLLLLLL pitch L
	ld (&FF13),a

	ld a,%11000110	;%IC---HHH	C1 Initial / Counter 1=stop / pitch H
	or b
	ld (&FF14),a
	ret
	
	
BeepChannel1:
	push af
	push bc

	;shape of the tone. changes how it sounds.
	ld a,%11011111	;Wave Duty (Tone) & Sound Length (Higher is shorter 
	ld (&FF16),a	;- no effect unles C=1 in FF1E)

	;envelope makes it louder or quieter over time
	ld a,%11111000	;%VVVVDNNN C1 Volume / Direction 0=down / envelope Number
	ld (&FF17),a	;								(fade speed - higher is slower)

	ld a,c
	ld (&FF18),a ;%LLLLLLLL pitch L

	;bottom three bits are the higher part of the pitch
	;Counter bit must be set for sounds to stop
	ld a,%11000110	;%IC---HHH	C1 Initial / Counter 1=stop / pitch H
	or b
	ld (&FF19),a
	
	pop bc
	pop af
	ret
	

Tone:
	push af
	push bc
	
	ld a,%11011111	;Wave Duty (Tone) & Sound Length (Higher is shorter 
	ld (&FF16),a	;- no effect unles C=1 in FF1E)

	ld a,%11111000	;%VVVVDNNN C1 Volume / Direction 0=down / envelope Number
	ld (&FF17),a	;								(fade speed - higher is slower)

	ld a,c
	ld (&FF18),a


	ld a,%10000110	;%IC---HHH	C1 Initial / Counter 1=stop / pitch H
	or b
	ld (&FF19),a
	
	pop bc
	pop bc
	pop af
	ret
	
Spin:
	push af
	push bc
		DWait:
		ld a,(Speed)
		ld c,a
		;ld c,&20
		SpinWait:
		call Spin2
		dec c
		ld a,c
		cp 0
		jr nz,SpinWait
		
		dec d
		ld a,d
		cp 0
		jr nz,DWait
	pop bc
	pop af
	ret

Spin2:
	push af
	push bc
		ld a,(Speed)
		ld c,a
		;ld c,&30
		SpinWait2:
		dec c
		ld a,c
		cp 0
		jr nz,SpinWait2
	pop bc
	pop af
	ret

SetVram:
BitmapFont:
StopLCD:
	ret
	include ".\ResourceFIles\GB_V1_Functions.asm"
	include ".\ResourceFIles\GB_V1_Footer.asm"
