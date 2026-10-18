	.file	"q8-kernels.c"
	.text
	.section .rdata,"dr"
	.align 8
.LC0:
	.ascii "D:/compete/.codex-deploy/optimization/tg/q8-kernels.c\0"
.LC1:
	.ascii "n % qk == 0\0"
.LC2:
	.ascii "nrc == 1\0"
	.text
	.p2align 4
	.globl	q8_baseline
	.def	q8_baseline;	.scl	2;	.type	32;	.endef
	.seh_proc	q8_baseline
q8_baseline:
	subq	$40, %rsp
	.seh_stackalloc	40
	.seh_endprologue
	movq	88(%rsp), %r8
	movl	%ecx, %r11d
	andl	$31, %ecx
	jne	.L10
	cmpl	$1, 104(%rsp)
	jne	.L3
	movl	%r11d, %r10d
	xorl	%eax, %eax
	vpcmpeqd	%ymm4, %ymm4, %ymm4
	vxorps	%xmm3, %xmm3, %xmm3
	sarl	$5, %r10d
	vpsrlw	$15, %ymm4, %ymm4
	cmpl	$31, %r11d
	jle	.L5
	.p2align 4,,10
	.p2align 3
.L6:
	vpxor	%xmm5, %xmm5, %xmm5
	vpinsrw	$0, (%r9,%rax), %xmm5, %xmm0
	vcvtph2ps	%xmm0, %xmm0
	addl	$1, %ecx
	vpinsrw	$0, (%r8,%rax), %xmm5, %xmm1
	vcvtph2ps	%xmm1, %xmm1
	vmulss	%xmm0, %xmm1, %xmm1
	vmovdqu	2(%r9,%rax), %ymm5
	vmovdqu	2(%r8,%rax), %ymm2
	addq	$34, %rax
	cmpl	%ecx, %r10d
	vpsignb	%ymm5, %ymm5, %ymm0
	vpsignb	%ymm5, %ymm2, %ymm2
	vpmaddubsw	%ymm2, %ymm0, %ymm0
	vpmaddwd	%ymm0, %ymm4, %ymm0
	vbroadcastss	%xmm1, %ymm1
	vcvtdq2ps	%ymm0, %ymm0
	vfmadd231ps	%ymm0, %ymm1, %ymm3
	jg	.L6
.L5:
	vextractf128	$0x1, %ymm3, %xmm0
	vaddps	%xmm3, %xmm0, %xmm0
	vmovhlps	%xmm0, %xmm0, %xmm1
	vaddps	%xmm1, %xmm0, %xmm0
	vmovshdup	%xmm0, %xmm1
	vaddss	%xmm1, %xmm0, %xmm0
	vmovss	%xmm0, (%rdx)
	vzeroupper
	addq	$40, %rsp
	ret
.L10:
	leaq	.LC0(%rip), %rdx
	movl	$61, %r8d
	leaq	.LC1(%rip), %rcx
	call	*__imp__assert(%rip)
.L3:
	leaq	.LC0(%rip), %rdx
	movl	$62, %r8d
	leaq	.LC2(%rip), %rcx
	call	*__imp__assert(%rip)
	nop
	.seh_endproc
	.p2align 4
	.globl	q8_u2
	.def	q8_u2;	.scl	2;	.type	32;	.endef
	.seh_proc	q8_u2
q8_u2:
	subq	$72, %rsp
	.seh_stackalloc	72
	vmovaps	%xmm6, 32(%rsp)
	.seh_savexmm	%xmm6, 32
	vmovaps	%xmm7, 48(%rsp)
	.seh_savexmm	%xmm7, 48
	.seh_endprologue
	movl	%ecx, %r8d
	andl	$31, %ecx
	movq	%rdx, %r11
	jne	.L20
	cmpl	$1, 136(%rsp)
	jne	.L13
	testl	%r8d, %r8d
	vpcmpeqd	%ymm3, %ymm3, %ymm3
	movq	%r9, %rdx
	movq	120(%rsp), %rax
	leal	31(%r8), %r10d
	vpsrlw	$15, %ymm3, %ymm3
	vxorps	%xmm4, %xmm4, %xmm4
	cmovns	%r8d, %r10d
	sarl	$5, %r10d
	cmpl	$63, %r8d
	jle	.L15
	.p2align 4,,10
	.p2align 3
.L16:
	vpxor	%xmm7, %xmm7, %xmm7
	vmovdqu	2(%rdx), %ymm6
	vpinsrw	$0, (%rdx), %xmm7, %xmm1
	vpinsrw	$0, (%rax), %xmm7, %xmm0
	vcvtph2ps	%xmm1, %xmm1
	vmovdqu	2(%rax), %ymm5
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm1, %xmm0, %xmm0
	vpinsrw	$0, 34(%rdx), %xmm7, %xmm2
	vcvtph2ps	%xmm2, %xmm2
	leal	3(%rcx), %r8d
	addq	$68, %rdx
	vpinsrw	$0, 34(%rax), %xmm7, %xmm1
	vcvtph2ps	%xmm1, %xmm1
	vmulss	%xmm1, %xmm2, %xmm2
	vmovdqu	-32(%rdx), %ymm7
	vpsignb	%ymm6, %ymm5, %ymm5
	vpsignb	%ymm6, %ymm6, %ymm1
	addl	$2, %ecx
	vmovdqu	36(%rax), %ymm6
	vpmaddubsw	%ymm5, %ymm1, %ymm1
	vbroadcastss	%xmm0, %ymm0
	addq	$68, %rax
	vpmaddwd	%ymm1, %ymm3, %ymm1
	vpsignb	%ymm7, %ymm6, %ymm6
	cmpl	%r8d, %r10d
	vcvtdq2ps	%ymm1, %ymm5
	vpsignb	%ymm7, %ymm7, %ymm1
	vpmaddubsw	%ymm6, %ymm1, %ymm1
	vfmadd132ps	%ymm5, %ymm4, %ymm0
	vpmaddwd	%ymm1, %ymm3, %ymm1
	vbroadcastss	%xmm2, %ymm4
	vcvtdq2ps	%ymm1, %ymm1
	vfmadd132ps	%ymm1, %ymm0, %ymm4
	jg	.L16
	leal	-2(%r10), %ecx
	andl	$-2, %ecx
	addl	$2, %ecx
.L15:
	cmpl	%r10d, %ecx
	jge	.L17
	movslq	%ecx, %rcx
	movq	120(%rsp), %rax
	vpxor	%xmm3, %xmm3, %xmm3
	imulq	$34, %rcx, %rcx
	vpinsrw	$0, (%r9,%rcx), %xmm3, %xmm0
	vpinsrw	$0, (%rax,%rcx), %xmm3, %xmm1
	vcvtph2ps	%xmm0, %xmm0
	vcvtph2ps	%xmm1, %xmm1
	vmulss	%xmm1, %xmm0, %xmm0
	vmovdqu	2(%r9,%rcx), %ymm3
	vmovdqu	2(%rax,%rcx), %ymm1
	vpsignb	%ymm3, %ymm3, %ymm2
	vpsignb	%ymm3, %ymm1, %ymm1
	vpmaddubsw	%ymm1, %ymm2, %ymm2
	vpcmpeqd	%ymm1, %ymm1, %ymm1
	vpsrlw	$15, %ymm1, %ymm1
	vpmaddwd	%ymm2, %ymm1, %ymm1
	vbroadcastss	%xmm0, %ymm0
	vcvtdq2ps	%ymm1, %ymm1
	vfmadd231ps	%ymm1, %ymm0, %ymm4
.L17:
	vextractf128	$0x1, %ymm4, %xmm0
	vaddps	%xmm4, %xmm0, %xmm0
	vmovhlps	%xmm0, %xmm0, %xmm1
	vaddps	%xmm1, %xmm0, %xmm0
	vmovshdup	%xmm0, %xmm1
	vaddss	%xmm1, %xmm0, %xmm0
	vmovss	%xmm0, (%r11)
	vzeroupper
	vmovaps	32(%rsp), %xmm6
	vmovaps	48(%rsp), %xmm7
	addq	$72, %rsp
	ret
.L13:
	leaq	.LC0(%rip), %rdx
	movl	$130, %r8d
	leaq	.LC2(%rip), %rcx
	call	*__imp__assert(%rip)
.L20:
	leaq	.LC0(%rip), %rdx
	movl	$129, %r8d
	leaq	.LC1(%rip), %rcx
	call	*__imp__assert(%rip)
	nop
	.seh_endproc
	.p2align 4
	.globl	q8_u4
	.def	q8_u4;	.scl	2;	.type	32;	.endef
	.seh_proc	q8_u4
q8_u4:
	pushq	%rbx
	.seh_pushreg	%rbx
	addq	$-128, %rsp
	.seh_stackalloc	128
	vmovaps	%xmm6, 32(%rsp)
	.seh_savexmm	%xmm6, 32
	vmovaps	%xmm7, 48(%rsp)
	.seh_savexmm	%xmm7, 48
	vmovaps	%xmm8, 64(%rsp)
	.seh_savexmm	%xmm8, 64
	vmovaps	%xmm9, 80(%rsp)
	.seh_savexmm	%xmm9, 80
	vmovaps	%xmm10, 96(%rsp)
	.seh_savexmm	%xmm10, 96
	vmovaps	%xmm11, 112(%rsp)
	.seh_savexmm	%xmm11, 112
	.seh_endprologue
	movq	184(%rsp), %rbx
	movl	%ecx, %r8d
	andl	$31, %ecx
	movq	%rdx, %r11
	jne	.L31
	cmpl	$1, 200(%rsp)
	jne	.L23
	testl	%r8d, %r8d
	vpcmpeqd	%ymm3, %ymm3, %ymm3
	movq	%r9, %rdx
	movq	%rbx, %rax
	leal	31(%r8), %r10d
	vpsrlw	$15, %ymm3, %ymm3
	vxorps	%xmm5, %xmm5, %xmm5
	cmovns	%r8d, %r10d
	sarl	$5, %r10d
	cmpl	$127, %r8d
	jle	.L25
	.p2align 4,,10
	.p2align 3
.L26:
	vpxor	%xmm6, %xmm6, %xmm6
	vmovdqu	2(%rdx), %ymm7
	vpinsrw	$0, (%rdx), %xmm6, %xmm0
	vpinsrw	$0, (%rax), %xmm6, %xmm2
	vpinsrw	$0, 34(%rax), %xmm6, %xmm1
	vcvtph2ps	%xmm0, %xmm0
	vcvtph2ps	%xmm2, %xmm2
	vpinsrw	$0, 68(%rax), %xmm6, %xmm4
	vmulss	%xmm0, %xmm2, %xmm2
	vcvtph2ps	%xmm4, %xmm4
	vpinsrw	$0, 34(%rdx), %xmm6, %xmm0
	vcvtph2ps	%xmm1, %xmm1
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm0, %xmm1, %xmm1
	vpinsrw	$0, 68(%rdx), %xmm6, %xmm0
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm4, %xmm0, %xmm0
	vpinsrw	$0, 102(%rdx), %xmm6, %xmm4
	vpinsrw	$0, 102(%rax), %xmm6, %xmm6
	vcvtph2ps	%xmm4, %xmm4
	vcvtph2ps	%xmm6, %xmm6
	vmulss	%xmm6, %xmm4, %xmm6
	vmovdqu	2(%rax), %ymm4
	vpsignb	%ymm7, %ymm7, %ymm9
	vmovdqu	70(%rdx), %ymm10
	leal	7(%rcx), %r8d
	addl	$4, %ecx
	vbroadcastss	%xmm2, %ymm2
	vpsignb	%ymm7, %ymm4, %ymm4
	vmovdqu	36(%rdx), %ymm7
	vpmaddubsw	%ymm4, %ymm9, %ymm9
	vbroadcastss	%xmm1, %ymm1
	vmovdqu	36(%rax), %ymm4
	vpmaddwd	%ymm9, %ymm3, %ymm9
	vbroadcastss	%xmm0, %ymm0
	addq	$136, %rdx
	vpsignb	%ymm7, %ymm7, %ymm8
	vmovdqu	-32(%rdx), %ymm11
	addq	$136, %rax
	vcvtdq2ps	%ymm9, %ymm9
	vpsignb	%ymm7, %ymm4, %ymm4
	vpmaddubsw	%ymm4, %ymm8, %ymm8
	vmovdqu	-66(%rax), %ymm4
	vpsignb	%ymm10, %ymm10, %ymm7
	vfmadd132ps	%ymm9, %ymm5, %ymm2
	vpmaddwd	%ymm8, %ymm3, %ymm8
	vbroadcastss	%xmm6, %ymm5
	vpsignb	%ymm10, %ymm4, %ymm4
	vmovdqu	-32(%rax), %ymm10
	cmpl	%r8d, %r10d
	vpmaddubsw	%ymm4, %ymm7, %ymm7
	vpsignb	%ymm11, %ymm11, %ymm4
	vpmaddwd	%ymm7, %ymm3, %ymm7
	vcvtdq2ps	%ymm8, %ymm8
	vfmadd132ps	%ymm8, %ymm2, %ymm1
	vpsignb	%ymm11, %ymm10, %ymm10
	vpmaddubsw	%ymm10, %ymm4, %ymm4
	vcvtdq2ps	%ymm7, %ymm7
	vfmadd132ps	%ymm7, %ymm1, %ymm0
	vpmaddwd	%ymm4, %ymm3, %ymm4
	vcvtdq2ps	%ymm4, %ymm4
	vfmadd132ps	%ymm4, %ymm0, %ymm5
	jg	.L26
	leal	-4(%r10), %ecx
	andl	$-4, %ecx
	addl	$4, %ecx
.L25:
	cmpl	%ecx, %r10d
	jle	.L27
	vpxor	%xmm7, %xmm7, %xmm7
	leal	1(%rcx), %edx
	movslq	%ecx, %rax
	imulq	$34, %rax, %rax
	cmpl	%edx, %r10d
	vpinsrw	$0, (%r9,%rax), %xmm7, %xmm0
	vpinsrw	$0, (%rbx,%rax), %xmm7, %xmm1
	vcvtph2ps	%xmm0, %xmm0
	vcvtph2ps	%xmm1, %xmm1
	vmulss	%xmm0, %xmm1, %xmm1
	vmovdqu	2(%r9,%rax), %ymm3
	vmovdqu	2(%rbx,%rax), %ymm2
	vpsignb	%ymm3, %ymm3, %ymm0
	vpsignb	%ymm3, %ymm2, %ymm2
	vpmaddubsw	%ymm2, %ymm0, %ymm0
	vpcmpeqd	%ymm2, %ymm2, %ymm2
	vpsrlw	$15, %ymm2, %ymm2
	vpmaddwd	%ymm0, %ymm2, %ymm0
	vbroadcastss	%xmm1, %ymm1
	vcvtdq2ps	%ymm0, %ymm0
	vfmadd231ps	%ymm0, %ymm1, %ymm5
	jle	.L27
	vpinsrw	$0, 34(%rbx,%rax), %xmm7, %xmm1
	vcvtph2ps	%xmm1, %xmm1
	addl	$2, %ecx
	vpinsrw	$0, 34(%r9,%rax), %xmm7, %xmm0
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm0, %xmm1, %xmm1
	vmovdqu	36(%r9,%rax), %ymm4
	cmpl	%ecx, %r10d
	vmovdqu	36(%rbx,%rax), %ymm3
	vpsignb	%ymm4, %ymm4, %ymm0
	vpsignb	%ymm4, %ymm3, %ymm3
	vpmaddubsw	%ymm3, %ymm0, %ymm0
	vpmaddwd	%ymm0, %ymm2, %ymm0
	vbroadcastss	%xmm1, %ymm1
	vcvtdq2ps	%ymm0, %ymm0
	vfmadd231ps	%ymm0, %ymm1, %ymm5
	jle	.L27
	vpinsrw	$0, 68(%r9,%rax), %xmm7, %xmm1
	vcvtph2ps	%xmm1, %xmm1
	vpinsrw	$0, 68(%rbx,%rax), %xmm7, %xmm0
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm1, %xmm0, %xmm0
	vmovdqu	70(%r9,%rax), %ymm4
	vmovdqu	70(%rbx,%rax), %ymm3
	vpsignb	%ymm4, %ymm4, %ymm1
	vpsignb	%ymm4, %ymm3, %ymm3
	vpmaddubsw	%ymm3, %ymm1, %ymm1
	vpmaddwd	%ymm1, %ymm2, %ymm2
	vbroadcastss	%xmm0, %ymm0
	vcvtdq2ps	%ymm2, %ymm2
	vfmadd231ps	%ymm2, %ymm0, %ymm5
.L27:
	vextractf128	$0x1, %ymm5, %xmm0
	vaddps	%xmm5, %xmm0, %xmm0
	vmovhlps	%xmm0, %xmm0, %xmm1
	vaddps	%xmm1, %xmm0, %xmm0
	vmovshdup	%xmm0, %xmm1
	vaddss	%xmm1, %xmm0, %xmm0
	vmovss	%xmm0, (%r11)
	vzeroupper
	vmovaps	32(%rsp), %xmm6
	vmovaps	48(%rsp), %xmm7
	vmovaps	64(%rsp), %xmm8
	vmovaps	80(%rsp), %xmm9
	vmovaps	96(%rsp), %xmm10
	vmovaps	112(%rsp), %xmm11
	subq	$-128, %rsp
	popq	%rbx
	ret
.L23:
	leaq	.LC0(%rip), %rdx
	movl	$206, %r8d
	leaq	.LC2(%rip), %rcx
	call	*__imp__assert(%rip)
.L31:
	leaq	.LC0(%rip), %rdx
	movl	$205, %r8d
	leaq	.LC1(%rip), %rcx
	call	*__imp__assert(%rip)
	nop
	.seh_endproc
	.p2align 4
	.globl	q8_a2
	.def	q8_a2;	.scl	2;	.type	32;	.endef
	.seh_proc	q8_a2
q8_a2:
	subq	$88, %rsp
	.seh_stackalloc	88
	vmovaps	%xmm6, 32(%rsp)
	.seh_savexmm	%xmm6, 32
	vmovaps	%xmm7, 48(%rsp)
	.seh_savexmm	%xmm7, 48
	vmovaps	%xmm8, 64(%rsp)
	.seh_savexmm	%xmm8, 64
	.seh_endprologue
	movl	%ecx, %eax
	andl	$31, %ecx
	movq	%rdx, %r11
	jne	.L40
	cmpl	$1, 152(%rsp)
	jne	.L34
	leal	31(%rax), %r10d
	testl	%eax, %eax
	vxorps	%xmm4, %xmm4, %xmm4
	cmovns	%eax, %r10d
	sarl	$5, %r10d
	cmpl	$63, %eax
	jle	.L36
	movq	136(%rsp), %rax
	vxorps	%xmm4, %xmm4, %xmm4
	vpcmpeqd	%ymm3, %ymm3, %ymm3
	movq	%r9, %rdx
	vmovaps	%ymm4, %ymm5
	vpsrlw	$15, %ymm3, %ymm3
	.p2align 4,,10
	.p2align 3
.L37:
	vpxor	%xmm2, %xmm2, %xmm2
	vmovdqu	2(%rdx), %ymm7
	vpinsrw	$0, (%rdx), %xmm2, %xmm0
	vpinsrw	$0, (%rax), %xmm2, %xmm6
	vcvtph2ps	%xmm0, %xmm0
	vpinsrw	$0, 34(%rdx), %xmm2, %xmm1
	vcvtph2ps	%xmm6, %xmm6
	vmulss	%xmm0, %xmm6, %xmm6
	vcvtph2ps	%xmm1, %xmm1
	leal	3(%rcx), %r8d
	vmovdqu	36(%rdx), %ymm8
	addl	$2, %ecx
	vpinsrw	$0, 34(%rax), %xmm2, %xmm0
	vmovdqu	2(%rax), %ymm2
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm0, %xmm1, %xmm1
	vpsignb	%ymm7, %ymm7, %ymm0
	addq	$68, %rdx
	addq	$68, %rax
	vpsignb	%ymm7, %ymm2, %ymm2
	vmovdqu	-32(%rax), %ymm7
	vpmaddubsw	%ymm2, %ymm0, %ymm0
	cmpl	%r8d, %r10d
	vpmaddwd	%ymm0, %ymm3, %ymm0
	vbroadcastss	%xmm6, %ymm6
	vcvtdq2ps	%ymm0, %ymm2
	vpsignb	%ymm8, %ymm7, %ymm7
	vpsignb	%ymm8, %ymm8, %ymm0
	vpmaddubsw	%ymm7, %ymm0, %ymm0
	vpmaddwd	%ymm0, %ymm3, %ymm0
	vbroadcastss	%xmm1, %ymm1
	vfmadd231ps	%ymm2, %ymm6, %ymm5
	vcvtdq2ps	%ymm0, %ymm0
	vfmadd231ps	%ymm0, %ymm1, %ymm4
	jg	.L37
	leal	-2(%r10), %ecx
	vaddps	%ymm4, %ymm5, %ymm4
	andl	$-2, %ecx
	addl	$2, %ecx
.L36:
	cmpl	%r10d, %ecx
	jge	.L38
	movslq	%ecx, %rcx
	movq	136(%rsp), %rax
	vpxor	%xmm5, %xmm5, %xmm5
	imulq	$34, %rcx, %rcx
	vpinsrw	$0, (%r9,%rcx), %xmm5, %xmm0
	vpinsrw	$0, (%rax,%rcx), %xmm5, %xmm1
	vcvtph2ps	%xmm0, %xmm0
	vcvtph2ps	%xmm1, %xmm1
	vmulss	%xmm1, %xmm0, %xmm0
	vmovdqu	2(%r9,%rcx), %ymm3
	vmovdqu	2(%rax,%rcx), %ymm1
	vpsignb	%ymm3, %ymm3, %ymm2
	vpsignb	%ymm3, %ymm1, %ymm1
	vpmaddubsw	%ymm1, %ymm2, %ymm2
	vpcmpeqd	%ymm1, %ymm1, %ymm1
	vpsrlw	$15, %ymm1, %ymm1
	vpmaddwd	%ymm2, %ymm1, %ymm1
	vbroadcastss	%xmm0, %ymm0
	vcvtdq2ps	%ymm1, %ymm1
	vfmadd231ps	%ymm1, %ymm0, %ymm4
.L38:
	vextractf128	$0x1, %ymm4, %xmm0
	vaddps	%xmm4, %xmm0, %xmm0
	vmovhlps	%xmm0, %xmm0, %xmm1
	vaddps	%xmm1, %xmm0, %xmm0
	vmovshdup	%xmm0, %xmm1
	vaddss	%xmm1, %xmm0, %xmm0
	vmovss	%xmm0, (%r11)
	vzeroupper
	vmovaps	32(%rsp), %xmm6
	vmovaps	48(%rsp), %xmm7
	vmovaps	64(%rsp), %xmm8
	addq	$88, %rsp
	ret
.L34:
	leaq	.LC0(%rip), %rdx
	movl	$292, %r8d
	leaq	.LC2(%rip), %rcx
	call	*__imp__assert(%rip)
.L40:
	leaq	.LC0(%rip), %rdx
	movl	$291, %r8d
	leaq	.LC1(%rip), %rcx
	call	*__imp__assert(%rip)
	nop
	.seh_endproc
	.p2align 4
	.globl	q8_a4
	.def	q8_a4;	.scl	2;	.type	32;	.endef
	.seh_proc	q8_a4
q8_a4:
	pushq	%rbx
	.seh_pushreg	%rbx
	subq	$176, %rsp
	.seh_stackalloc	176
	vmovaps	%xmm6, 32(%rsp)
	.seh_savexmm	%xmm6, 32
	vmovaps	%xmm7, 48(%rsp)
	.seh_savexmm	%xmm7, 48
	vmovaps	%xmm8, 64(%rsp)
	.seh_savexmm	%xmm8, 64
	vmovaps	%xmm9, 80(%rsp)
	.seh_savexmm	%xmm9, 80
	vmovaps	%xmm10, 96(%rsp)
	.seh_savexmm	%xmm10, 96
	vmovaps	%xmm11, 112(%rsp)
	.seh_savexmm	%xmm11, 112
	vmovaps	%xmm12, 128(%rsp)
	.seh_savexmm	%xmm12, 128
	vmovaps	%xmm13, 144(%rsp)
	.seh_savexmm	%xmm13, 144
	vmovaps	%xmm14, 160(%rsp)
	.seh_savexmm	%xmm14, 160
	.seh_endprologue
	movq	232(%rsp), %rbx
	movl	%ecx, %eax
	andl	$31, %ecx
	movq	%rdx, %r11
	jne	.L50
	cmpl	$1, 248(%rsp)
	jne	.L43
	leal	31(%rax), %r10d
	testl	%eax, %eax
	vxorps	%xmm5, %xmm5, %xmm5
	cmovns	%eax, %r10d
	sarl	$5, %r10d
	cmpl	$127, %eax
	jle	.L45
	vxorps	%xmm7, %xmm7, %xmm7
	vpcmpeqd	%ymm4, %ymm4, %ymm4
	movq	%r9, %rdx
	movq	%rbx, %rax
	vmovaps	%ymm7, %ymm6
	vmovaps	%ymm7, %ymm5
	vmovaps	%ymm7, %ymm8
	vpsrlw	$15, %ymm4, %ymm4
	.p2align 4,,10
	.p2align 3
.L46:
	vpxor	%xmm1, %xmm1, %xmm1
	vpinsrw	$0, (%rdx), %xmm1, %xmm0
	vpinsrw	$0, (%rax), %xmm1, %xmm12
	vpinsrw	$0, 34(%rdx), %xmm1, %xmm10
	vmovdqa	%xmm1, %xmm2
	vcvtph2ps	%xmm0, %xmm0
	vcvtph2ps	%xmm12, %xmm12
	vpinsrw	$0, 68(%rdx), %xmm1, %xmm3
	vmulss	%xmm0, %xmm12, %xmm12
	vcvtph2ps	%xmm10, %xmm10
	vpinsrw	$0, 34(%rax), %xmm1, %xmm0
	vcvtph2ps	%xmm3, %xmm3
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm0, %xmm10, %xmm10
	vpinsrw	$0, 68(%rax), %xmm1, %xmm0
	vpinsrw	$0, 102(%rdx), %xmm1, %xmm1
	vcvtph2ps	%xmm0, %xmm0
	vcvtph2ps	%xmm1, %xmm1
	vmulss	%xmm0, %xmm3, %xmm3
	vpinsrw	$0, 102(%rax), %xmm2, %xmm0
	vmovdqu	2(%rdx), %ymm2
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm0, %xmm1, %xmm1
	addq	$136, %rdx
	vmovdqu	2(%rax), %ymm0
	leal	7(%rcx), %r8d
	vbroadcastss	%xmm12, %ymm12
	addl	$4, %ecx
	vpsignb	%ymm2, %ymm2, %ymm11
	vmovdqu	-66(%rdx), %ymm13
	vbroadcastss	%xmm10, %ymm10
	addq	$136, %rax
	vpsignb	%ymm2, %ymm0, %ymm0
	vmovdqu	-100(%rdx), %ymm2
	vpmaddubsw	%ymm0, %ymm11, %ymm11
	vbroadcastss	%xmm3, %ymm3
	vmovdqu	-100(%rax), %ymm0
	vpmaddwd	%ymm11, %ymm4, %ymm11
	vbroadcastss	%xmm1, %ymm1
	vpsignb	%ymm2, %ymm2, %ymm9
	vmovdqu	-32(%rdx), %ymm14
	vcvtdq2ps	%ymm11, %ymm11
	vfmadd231ps	%ymm11, %ymm12, %ymm8
	vpsignb	%ymm2, %ymm0, %ymm0
	vpmaddubsw	%ymm0, %ymm9, %ymm9
	vmovdqu	-66(%rax), %ymm0
	vpsignb	%ymm13, %ymm13, %ymm2
	vpmaddwd	%ymm9, %ymm4, %ymm9
	vpsignb	%ymm13, %ymm0, %ymm0
	vmovdqu	-32(%rax), %ymm13
	cmpl	%r8d, %r10d
	vpmaddubsw	%ymm0, %ymm2, %ymm2
	vpsignb	%ymm14, %ymm14, %ymm0
	vpmaddwd	%ymm2, %ymm4, %ymm2
	vcvtdq2ps	%ymm9, %ymm9
	vfmadd231ps	%ymm9, %ymm10, %ymm5
	vpsignb	%ymm14, %ymm13, %ymm13
	vpmaddubsw	%ymm13, %ymm0, %ymm0
	vcvtdq2ps	%ymm2, %ymm2
	vfmadd231ps	%ymm2, %ymm3, %ymm6
	vpmaddwd	%ymm0, %ymm4, %ymm0
	vcvtdq2ps	%ymm0, %ymm0
	vfmadd231ps	%ymm0, %ymm1, %ymm7
	jg	.L46
	vaddps	%ymm8, %ymm5, %ymm5
	leal	-4(%r10), %ecx
	vaddps	%ymm7, %ymm6, %ymm6
	andl	$-4, %ecx
	addl	$4, %ecx
	vaddps	%ymm6, %ymm5, %ymm5
.L45:
	cmpl	%ecx, %r10d
	jle	.L47
	vpxor	%xmm7, %xmm7, %xmm7
	leal	1(%rcx), %edx
	movslq	%ecx, %rax
	imulq	$34, %rax, %rax
	cmpl	%edx, %r10d
	vpinsrw	$0, (%r9,%rax), %xmm7, %xmm0
	vpinsrw	$0, (%rbx,%rax), %xmm7, %xmm1
	vcvtph2ps	%xmm0, %xmm0
	vcvtph2ps	%xmm1, %xmm1
	vmulss	%xmm0, %xmm1, %xmm1
	vmovdqu	2(%r9,%rax), %ymm3
	vmovdqu	2(%rbx,%rax), %ymm2
	vpsignb	%ymm3, %ymm3, %ymm0
	vpsignb	%ymm3, %ymm2, %ymm2
	vpmaddubsw	%ymm2, %ymm0, %ymm0
	vpcmpeqd	%ymm2, %ymm2, %ymm2
	vpsrlw	$15, %ymm2, %ymm2
	vpmaddwd	%ymm0, %ymm2, %ymm0
	vbroadcastss	%xmm1, %ymm1
	vcvtdq2ps	%ymm0, %ymm0
	vfmadd231ps	%ymm0, %ymm1, %ymm5
	jle	.L47
	vpinsrw	$0, 34(%rbx,%rax), %xmm7, %xmm1
	vcvtph2ps	%xmm1, %xmm1
	addl	$2, %ecx
	vpinsrw	$0, 34(%r9,%rax), %xmm7, %xmm0
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm0, %xmm1, %xmm1
	vmovdqu	36(%r9,%rax), %ymm4
	cmpl	%ecx, %r10d
	vmovdqu	36(%rbx,%rax), %ymm3
	vpsignb	%ymm4, %ymm4, %ymm0
	vpsignb	%ymm4, %ymm3, %ymm3
	vpmaddubsw	%ymm3, %ymm0, %ymm0
	vpmaddwd	%ymm0, %ymm2, %ymm0
	vbroadcastss	%xmm1, %ymm1
	vcvtdq2ps	%ymm0, %ymm0
	vfmadd231ps	%ymm0, %ymm1, %ymm5
	jle	.L47
	vpinsrw	$0, 68(%r9,%rax), %xmm7, %xmm1
	vcvtph2ps	%xmm1, %xmm1
	vpinsrw	$0, 68(%rbx,%rax), %xmm7, %xmm0
	vcvtph2ps	%xmm0, %xmm0
	vmulss	%xmm1, %xmm0, %xmm0
	vmovdqu	70(%r9,%rax), %ymm4
	vmovdqu	70(%rbx,%rax), %ymm3
	vpsignb	%ymm4, %ymm4, %ymm1
	vpsignb	%ymm4, %ymm3, %ymm3
	vpmaddubsw	%ymm3, %ymm1, %ymm1
	vpmaddwd	%ymm1, %ymm2, %ymm2
	vbroadcastss	%xmm0, %ymm0
	vcvtdq2ps	%ymm2, %ymm2
	vfmadd231ps	%ymm2, %ymm0, %ymm5
.L47:
	vextractf128	$0x1, %ymm5, %xmm0
	vaddps	%xmm5, %xmm0, %xmm0
	vmovhlps	%xmm0, %xmm0, %xmm1
	vaddps	%xmm1, %xmm0, %xmm0
	vmovshdup	%xmm0, %xmm1
	vaddss	%xmm1, %xmm0, %xmm0
	vmovss	%xmm0, (%r11)
	vzeroupper
	vmovaps	32(%rsp), %xmm6
	vmovaps	48(%rsp), %xmm7
	vmovaps	64(%rsp), %xmm8
	vmovaps	80(%rsp), %xmm9
	vmovaps	96(%rsp), %xmm10
	vmovaps	112(%rsp), %xmm11
	vmovaps	128(%rsp), %xmm12
	vmovaps	144(%rsp), %xmm13
	vmovaps	160(%rsp), %xmm14
	addq	$176, %rsp
	popq	%rbx
	ret
.L43:
	leaq	.LC0(%rip), %rdx
	movl	$371, %r8d
	leaq	.LC2(%rip), %rcx
	call	*__imp__assert(%rip)
.L50:
	leaq	.LC0(%rip), %rdx
	movl	$370, %r8d
	leaq	.LC1(%rip), %rcx
	call	*__imp__assert(%rip)
	nop
	.seh_endproc
	.ident	"GCC: (x86_64-win32-seh-rev1, Built by MinGW-Builds project) 15.2.0"
