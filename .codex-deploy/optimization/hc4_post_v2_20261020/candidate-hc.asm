
/work/apac2602/qwen38-cpu/optimization/20261020-hc4-post-v2/sources/hc4-post-v2-4340917/build/bin/libggml-cpu.so:     file format elf64-x86-64


Disassembly of section .text:

0000000000129090 <ggml_compute_forward_dsv4_hc_post>:
  129090:	push   %rbp
  129091:	mov    %rsp,%rbp
  129094:	and    $0xffffffffffffffe0,%rsp
  129098:	push   %r12
  12909a:	push   %r13
  12909c:	push   %r14
  12909e:	push   %r15
  1290a0:	push   %rbx
  1290a1:	sub    $0x98,%rsp
  1290a8:	mov    %rdi,%rdx
  1290ab:	mov    0x98(%rsi),%r14
  1290b2:	cmpl   $0x0,(%r14)
  1290b6:	jne    1293d6 <ggml_compute_forward_dsv4_hc_post+0x346>
  1290bc:	mov    0xa0(%rsi),%rcx
  1290c3:	mov    0xa8(%rsi),%r13
  1290ca:	mov    0xb0(%rsi),%r10
  1290d1:	cmpl   $0x0,(%rcx)
  1290d4:	jne    12988c <ggml_compute_forward_dsv4_hc_post+0x7fc>
  1290da:	cmpl   $0x0,0x0(%r13)
  1290df:	jne    12986b <ggml_compute_forward_dsv4_hc_post+0x7db>
  1290e5:	cmpl   $0x0,(%rsi)
  1290e8:	jne    12984a <ggml_compute_forward_dsv4_hc_post+0x7ba>
  1290ee:	mov    0x10(%r14),%r9
  1290f2:	mov    0x18(%r14),%r12
  1290f6:	mov    0x18(%rcx),%r8
  1290fa:	cmp    0x10(%rsi),%r9
  1290fe:	jne    129829 <ggml_compute_forward_dsv4_hc_post+0x799>
  129104:	cmp    0x18(%rsi),%r8
  129108:	jne    129808 <ggml_compute_forward_dsv4_hc_post+0x778>
  12910e:	cmp    0x20(%rsi),%r12
  129112:	jne    1297e7 <ggml_compute_forward_dsv4_hc_post+0x757>
  129118:	cmp    0x10(%rcx),%r9
  12911c:	jne    1297c6 <ggml_compute_forward_dsv4_hc_post+0x736>
  129122:	cmp    0x20(%rcx),%r12
  129126:	jne    1297a5 <ggml_compute_forward_dsv4_hc_post+0x715>
  12912c:	cmp    0x10(%r13),%r8
  129130:	jne    129784 <ggml_compute_forward_dsv4_hc_post+0x6f4>
  129136:	cmp    0x18(%r13),%r12
  12913a:	jne    129763 <ggml_compute_forward_dsv4_hc_post+0x6d3>
  129140:	xor    %ebx,%ebx
  129142:	xor    %edi,%edi
  129144:	xor    %eax,%eax
  129146:	test   %r10,%r10
  129149:	je     12917f <ggml_compute_forward_dsv4_hc_post+0xef>
  12914b:	cmpl   $0x0,(%r10)
  12914f:	jne    129742 <ggml_compute_forward_dsv4_hc_post+0x6b2>
  129155:	cmp    0x10(%r10),%r8
  129159:	jne    129721 <ggml_compute_forward_dsv4_hc_post+0x691>
  12915f:	cmp    0x18(%r10),%r8
  129163:	jne    129700 <ggml_compute_forward_dsv4_hc_post+0x670>
  129169:	cmp    0x20(%r10),%r12
  12916d:	jne    1296df <ggml_compute_forward_dsv4_hc_post+0x64f>
  129173:	mov    0x30(%r10),%rbx
  129177:	mov    0x38(%r10),%rdi
  12917b:	mov    0x40(%r10),%rax
  12917f:	mov    0x30(%r14),%r11
  129183:	mov    %r11,0x20(%rsp)
  129188:	mov    0x38(%r14),%r15
  12918c:	mov    0x30(%rcx),%r11
  129190:	mov    %r15,0x60(%rsp)
  129195:	mov    %r11,(%rsp)
  129199:	test   %rcx,%rcx
  12919c:	je     1291b2 <ggml_compute_forward_dsv4_hc_post+0x122>
  12919e:	mov    0x38(%rcx),%r11
  1291a2:	mov    0x40(%rcx),%r15
  1291a6:	mov    %r11,0x30(%rsp)
  1291ab:	mov    %r15,0x58(%rsp)
  1291b0:	jmp    1291bf <ggml_compute_forward_dsv4_hc_post+0x12f>
  1291b2:	xor    %r11d,%r11d
  1291b5:	mov    %r11,0x30(%rsp)
  1291ba:	mov    %r11,0x58(%rsp)
  1291bf:	test   %r13,%r13
  1291c2:	je     1291d8 <ggml_compute_forward_dsv4_hc_post+0x148>
  1291c4:	mov    0x30(%r13),%r11
  1291c8:	mov    0x38(%r13),%r15
  1291cc:	mov    %r11,0x70(%rsp)
  1291d1:	mov    %r15,0x68(%rsp)
  1291d6:	jmp    1291e5 <ggml_compute_forward_dsv4_hc_post+0x155>
  1291d8:	xor    %r11d,%r11d
  1291db:	mov    %r11,0x70(%rsp)
  1291e0:	mov    %r11,0x68(%rsp)
  1291e5:	test   %rsi,%rsi
  1291e8:	je     12920d <ggml_compute_forward_dsv4_hc_post+0x17d>
  1291ea:	mov    0x30(%rsi),%r11
  1291ee:	mov    %r11,0x90(%rsp)
  1291f6:	mov    0x38(%rsi),%r15
  1291fa:	mov    0x40(%rsi),%r11
  1291fe:	mov    %r15,0x80(%rsp)
  129206:	mov    %r11,0x78(%rsp)
  12920b:	jmp    129225 <ggml_compute_forward_dsv4_hc_post+0x195>
  12920d:	xor    %r11d,%r11d
  129210:	mov    %r11,0x90(%rsp)
  129218:	mov    %r11,0x80(%rsp)
  129220:	mov    %r11,0x78(%rsp)
  129225:	imul   %r9,%r12
  129229:	imul   %r8,%r12
  12922d:	movslq 0x4(%rdx),%r15
  129231:	mov    %rax,0x38(%rsp)
  129236:	movslq (%rdx),%r11
  129239:	lea    -0x1(%r15,%r12,1),%rax
  12923e:	cqto   
  129240:	idiv   %r15
  129243:	imul   %rax,%r11
  129247:	add    %r11,%rax
  12924a:	cmp    %r12,%rax
  12924d:	cmovl  %rax,%r12
  129251:	mov    0x38(%rsp),%rax
  129256:	cmp    $0x4,%r8
  12925a:	je     129422 <ggml_compute_forward_dsv4_hc_post+0x392>
  129260:	cmp    %r12,%r11
  129263:	jge    1293be <ggml_compute_forward_dsv4_hc_post+0x32e>
  129269:	mov    0xf8(%r14),%rdx
  129270:	mov    0xf8(%r13),%r14
  129277:	mov    0xf8(%rsi),%r13
  12927e:	mov    %r9,%rsi
  129281:	mov    %rdi,0x48(%rsp)
  129286:	imul   %r8,%rsi
  12928a:	mov    %r13,0x28(%rsp)
  12928f:	mov    %r14,0x8(%rsp)
  129294:	mov    %rdx,0x10(%rsp)
  129299:	mov    %r12,0x88(%rsp)
  1292a1:	mov    %rax,0x38(%rsp)
  1292a6:	mov    %rbx,0x40(%rsp)
  1292ab:	mov    %r9,0x18(%rsp)
  1292b0:	mov    %rcx,0x50(%rsp)
  1292b5:	mov    0x30(%rsp),%rdi
  1292ba:	mov    %r11,%rax
  1292bd:	cqto   
  1292bf:	idivq  0x18(%rsp)
  1292c4:	mov    %rdx,%rcx
  1292c7:	cqto   
  1292c9:	idiv   %r8
  1292cc:	mov    %r11,%rax
  1292cf:	mov    %rdx,%rbx
  1292d2:	cqto   
  1292d4:	idiv   %rsi
  1292d7:	mov    0x20(%rsp),%r12
  1292dc:	mov    %rax,%r14
  1292df:	imul   %rcx,%r12
  1292e3:	mov    0x70(%rsp),%r15
  1292e8:	imul   %rbx,%r15
  1292ec:	mov    0x60(%rsp),%r9
  1292f1:	imul   %r14,%r9
  1292f5:	mov    0x68(%rsp),%r13
  1292fa:	imul   %r14,%r13
  1292fe:	add    0x10(%rsp),%r12
  129303:	add    0x8(%rsp),%r15
  129308:	vmovss (%r9,%r12,1),%xmm0
  12930e:	vmulss 0x0(%r13,%r15,1),%xmm0,%xmm0
  129315:	test   %r10,%r10
  129318:	je     1293f0 <ggml_compute_forward_dsv4_hc_post+0x360>
  12931e:	xor    %r9d,%r9d
  129321:	xor    %r12d,%r12d
  129324:	xor    %r13d,%r13d
  129327:	test   %r8,%r8
  12932a:	jle    129388 <ggml_compute_forward_dsv4_hc_post+0x2f8>
  12932c:	mov    %rcx,%rdx
  12932f:	mov    %r14,%rax
  129332:	imul   (%rsp),%rdx
  129337:	imul   0x58(%rsp),%rax
  12933d:	mov    0x50(%rsp),%r15
  129342:	add    %rax,%rdx
  129345:	mov    %rbx,%rax
  129348:	imul   0x40(%rsp),%rax
  12934e:	add    0xf8(%r15),%rdx
  129355:	mov    %r14,%r15
  129358:	imul   0x38(%rsp),%r15
  12935e:	add    %r15,%rax
  129361:	mov    0x48(%rsp),%r15
  129366:	add    0xf8(%r10),%rax
  12936d:	vmovss 0x0(%r13,%rax,1),%xmm1
  129374:	inc    %r9
  129377:	vfmadd231ss (%r12,%rdx,1),%xmm1,%xmm0
  12937d:	add    %rdi,%r12
  129380:	add    %r15,%r13
  129383:	cmp    %r8,%r9
  129386:	jl     12936d <ggml_compute_forward_dsv4_hc_post+0x2dd>
  129388:	imul   0x80(%rsp),%rbx
  129391:	imul   0x78(%rsp),%r14
  129397:	imul   0x90(%rsp),%rcx
  1293a0:	add    %r14,%rbx
  1293a3:	inc    %r11
  1293a6:	add    0x28(%rsp),%rcx
  1293ab:	vmovss %xmm0,(%rbx,%rcx,1)
  1293b0:	cmp    0x88(%rsp),%r11
  1293b8:	jl     1292ba <ggml_compute_forward_dsv4_hc_post+0x22a>
  1293be:	vzeroupper 
  1293c1:	add    $0x98,%rsp
  1293c8:	pop    %rbx
  1293c9:	pop    %r15
  1293cb:	pop    %r14
  1293cd:	pop    %r13
  1293cf:	pop    %r12
  1293d1:	mov    %rbp,%rsp
  1293d4:	pop    %rbp
  1293d5:	retq   
  1293d6:	lea    0x8c6a3(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  1293dd:	mov    $0x2dc3,%esi
  1293e2:	lea    0x784af(%rip),%rdx        # 1a1898 <il0_peep_printf_format_0+0x5c>
  1293e9:	xor    %eax,%eax
  1293eb:	callq  159a0 <ggml_abort@plt>
  1293f0:	mov    %rbx,%r9
  1293f3:	mov    %r14,%rdx
  1293f6:	mov    %rcx,%r12
  1293f9:	imul   %rdi,%r9
  1293fd:	imul   0x58(%rsp),%rdx
  129403:	imul   (%rsp),%r12
  129408:	mov    0x50(%rsp),%rax
  12940d:	add    %rdx,%r9
  129410:	add    0xf8(%rax),%r12
  129417:	vaddss (%r9,%r12,1),%xmm0,%xmm0
  12941d:	jmpq   129388 <ggml_compute_forward_dsv4_hc_post+0x2f8>
  129422:	cmpq   $0x4,0x20(%rsp)
  129428:	jne    129260 <ggml_compute_forward_dsv4_hc_post+0x1d0>
  12942e:	cmpq   $0x4,(%rsp)
  129433:	jne    129260 <ggml_compute_forward_dsv4_hc_post+0x1d0>
  129439:	cmpq   $0x4,0x90(%rsp)
  129442:	jne    129260 <ggml_compute_forward_dsv4_hc_post+0x1d0>
  129448:	cmp    %r12,%r11
  12944b:	jge    1293be <ggml_compute_forward_dsv4_hc_post+0x32e>
  129451:	mov    0x30(%rsp),%r15
  129456:	lea    (%rdi,%rdi,2),%rdx
  12945a:	mov    %rdx,(%rsp)
  12945e:	mov    %rax,0x38(%rsp)
  129463:	mov    %rdi,0x48(%rsp)
  129468:	lea    (%r15,%r15,1),%r8
  12946c:	mov    %r8,0x8(%rsp)
  129471:	lea    (%r15,%r15,2),%r15
  129475:	mov    %r15,0x10(%rsp)
  12947a:	mov    %rbx,0x40(%rsp)
  12947f:	mov    %r13,0x18(%rsp)
  129484:	mov    %rcx,0x50(%rsp)
  129489:	mov    %r14,0x20(%rsp)
  12948e:	mov    %rsi,0x28(%rsp)
  129493:	mov    %r11,%rax
  129496:	mov    %r12,%rdi
  129499:	cqto   
  12949b:	sub    %r11,%rdi
  12949e:	idiv   %r9
  1294a1:	mov    %rax,%r8
  1294a4:	mov    %rdx,%rcx
  1294a7:	mov    %r8,%r13
  1294aa:	sar    %r13
  1294ad:	shr    $0x3e,%r13
  1294b1:	add    %r8,%r13
  1294b4:	mov    %r13,%rsi
  1294b7:	sar    $0x2,%r13
  1294bb:	and    $0xfffffffffffffffc,%rsi
  1294bf:	mov    0x60(%rsp),%r15
  1294c4:	sub    %rsi,%r8
  1294c7:	imul   %r13,%r15
  1294cb:	mov    0x20(%rsp),%rbx
  1294d0:	mov    %r9,%rsi
  1294d3:	sub    %rcx,%rsi
  1294d6:	mov    0x28(%rsp),%rax
  1294db:	cmp    %rsi,%rdi
  1294de:	mov    0xf8(%rbx),%r14
  1294e5:	cmovl  %rdi,%rsi
  1294e9:	mov    0x58(%rsp),%rdx
  1294ee:	imul   %r13,%rdx
  1294f2:	mov    0x50(%rsp),%rbx
  1294f7:	lea    (%r14,%rcx,4),%rdi
  1294fb:	mov    0xf8(%rax),%r14
  129502:	add    %r15,%rdi
  129505:	mov    0x80(%rsp),%r15
  12950d:	mov    0x78(%rsp),%rax
  129512:	imul   %r8,%r15
  129516:	imul   %r13,%rax
  12951a:	add    0xf8(%rbx),%rdx
  129521:	lea    (%r14,%rcx,4),%rbx
  129525:	add    %rax,%r15
  129528:	add    %r15,%rbx
  12952b:	mov    0x70(%rsp),%r15
  129530:	imul   %r8,%r15
  129534:	mov    0x68(%rsp),%r14
  129539:	imul   %r13,%r14
  12953d:	mov    0x18(%rsp),%rax
  129542:	add    0xf8(%rax),%r15
  129549:	xor    %eax,%eax
  12954b:	vmovss (%r14,%r15,1),%xmm1
  129551:	vbroadcastss %xmm1,%ymm0
  129556:	test   %r10,%r10
  129559:	je     12967a <ggml_compute_forward_dsv4_hc_post+0x5ea>
  12955f:	imul   0x40(%rsp),%r8
  129565:	imul   0x38(%rsp),%r13
  12956b:	add    0xf8(%r10),%r8
  129572:	add    %r13,%r8
  129575:	mov    0x48(%rsp),%r13
  12957a:	mov    (%rsp),%r14
  12957e:	mov    0x8(%rsp),%r15
  129583:	vmovss (%r8),%xmm9
  129588:	vmovss (%r8,%r13,1),%xmm8
  12958e:	vmovss (%r8,%r13,2),%xmm7
  129594:	lea    (%rdx,%rcx,4),%r13
  129598:	vmovss (%r14,%r8,1),%xmm6
  12959e:	mov    0x30(%rsp),%r8
  1295a3:	vbroadcastss %xmm9,%ymm5
  1295a8:	vbroadcastss %xmm8,%ymm4
  1295ad:	vbroadcastss %xmm7,%ymm3
  1295b2:	vbroadcastss %xmm6,%ymm2
  1295b7:	lea    (%r8,%rcx,4),%r14
  1295bb:	add    %rdx,%r14
  1295be:	lea    (%r15,%rcx,4),%r8
  1295c2:	mov    0x10(%rsp),%r15
  1295c7:	add    %rdx,%r8
  1295ca:	lea    (%r15,%rcx,4),%rcx
  1295ce:	add    %rdx,%rcx
  1295d1:	cmp    $0x8,%rsi
  1295d5:	jl     12960b <ggml_compute_forward_dsv4_hc_post+0x57b>
  1295d7:	mov    $0x8,%edx
  1295dc:	vmulps (%rdi,%rax,4),%ymm0,%ymm10
  1295e1:	vfmadd231ps 0x0(%r13,%rax,4),%ymm5,%ymm10
  1295e8:	vfmadd231ps (%r14,%rax,4),%ymm4,%ymm10
  1295ee:	vfmadd231ps (%r8,%rax,4),%ymm3,%ymm10
  1295f4:	vfmadd231ps (%rcx,%rax,4),%ymm2,%ymm10
  1295fa:	vmovups %ymm10,(%rbx,%rax,4)
  1295ff:	mov    %rdx,%rax
  129602:	add    $0x8,%rdx
  129606:	cmp    %rsi,%rdx
  129609:	jle    1295dc <ggml_compute_forward_dsv4_hc_post+0x54c>
  12960b:	lea    0x0(,%rax,4),%rdx
  129613:	cmp    %rsi,%rax
  129616:	jge    129669 <ggml_compute_forward_dsv4_hc_post+0x5d9>
  129618:	nopl   0x0(%rax,%rax,1)
  129620:	vmovss (%rdx,%rdi,1),%xmm16
  129627:	inc    %rax
  12962a:	vmulss %xmm1,%xmm16,%xmm0
  129630:	vmovss (%rdx,%r13,1),%xmm2
  129636:	vfmadd213ss %xmm0,%xmm9,%xmm2
  12963b:	vmovss (%rdx,%r14,1),%xmm3
  129641:	vmovss (%rdx,%r8,1),%xmm4
  129647:	vmovss (%rdx,%rcx,1),%xmm5
  12964c:	vfmadd213ss %xmm2,%xmm8,%xmm3
  129651:	vfmadd213ss %xmm3,%xmm7,%xmm4
  129656:	vfmadd213ss %xmm4,%xmm6,%xmm5
  12965b:	vmovss %xmm5,(%rdx,%rbx,1)
  129660:	add    $0x4,%rdx
  129664:	cmp    %rsi,%rax
  129667:	jl     129620 <ggml_compute_forward_dsv4_hc_post+0x590>
  129669:	add    %rsi,%r11
  12966c:	cmp    %r12,%r11
  12966f:	jl     129493 <ggml_compute_forward_dsv4_hc_post+0x403>
  129675:	jmpq   1293be <ggml_compute_forward_dsv4_hc_post+0x32e>
  12967a:	imul   0x30(%rsp),%r8
  129680:	lea    (%r8,%rcx,4),%rcx
  129684:	add    %rdx,%rcx
  129687:	cmp    $0x8,%rsi
  12968b:	jl     1296ad <ggml_compute_forward_dsv4_hc_post+0x61d>
  12968d:	mov    $0x8,%edx
  129692:	vmulps (%rdi,%rax,4),%ymm0,%ymm2
  129697:	vaddps (%rcx,%rax,4),%ymm2,%ymm3
  12969c:	vmovups %ymm3,(%rbx,%rax,4)
  1296a1:	mov    %rdx,%rax
  1296a4:	add    $0x8,%rdx
  1296a8:	cmp    %rsi,%rdx
  1296ab:	jle    129692 <ggml_compute_forward_dsv4_hc_post+0x602>
  1296ad:	lea    0x0(,%rax,4),%rdx
  1296b5:	cmp    %rsi,%rax
  1296b8:	jge    129669 <ggml_compute_forward_dsv4_hc_post+0x5d9>
  1296ba:	vmovss (%rdx,%rdi,1),%xmm16
  1296c1:	inc    %rax
  1296c4:	vmulss %xmm1,%xmm16,%xmm0
  1296ca:	vaddss (%rdx,%rcx,1),%xmm0,%xmm2
  1296cf:	vmovss %xmm2,(%rdx,%rbx,1)
  1296d4:	add    $0x4,%rdx
  1296d8:	cmp    %rsi,%rax
  1296db:	jl     1296ba <ggml_compute_forward_dsv4_hc_post+0x62a>
  1296dd:	jmp    129669 <ggml_compute_forward_dsv4_hc_post+0x5d9>
  1296df:	lea    0x8c39a(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  1296e6:	mov    $0x2d49,%esi
  1296eb:	lea    0x78176(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  1296f2:	lea    0x8dbc3(%rip),%rcx        # 1b72bc <dst.25588.0.0.384+0x1abc>
  1296f9:	xor    %eax,%eax
  1296fb:	callq  159a0 <ggml_abort@plt>
  129700:	lea    0x8c379(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  129707:	mov    $0x2d48,%esi
  12970c:	lea    0x78155(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  129713:	lea    0x8dbba(%rip),%rcx        # 1b72d4 <dst.25588.0.0.384+0x1ad4>
  12971a:	xor    %eax,%eax
  12971c:	callq  159a0 <ggml_abort@plt>
  129721:	lea    0x8c358(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  129728:	mov    $0x2d47,%esi
  12972d:	lea    0x78134(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  129734:	lea    0x8dbad(%rip),%rcx        # 1b72e8 <dst.25588.0.0.384+0x1ae8>
  12973b:	xor    %eax,%eax
  12973d:	callq  159a0 <ggml_abort@plt>
  129742:	lea    0x8c337(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  129749:	mov    $0x2d46,%esi
  12974e:	lea    0x78113(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  129755:	lea    0x8dba0(%rip),%rcx        # 1b72fc <dst.25588.0.0.384+0x1afc>
  12975c:	xor    %eax,%eax
  12975e:	callq  159a0 <ggml_abort@plt>
  129763:	lea    0x8c316(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  12976a:	mov    $0x2d3f,%esi
  12976f:	lea    0x780f2(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  129776:	lea    0x8db9b(%rip),%rcx        # 1b7318 <dst.25588.0.0.384+0x1b18>
  12977d:	xor    %eax,%eax
  12977f:	callq  159a0 <ggml_abort@plt>
  129784:	lea    0x8c2f5(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  12978b:	mov    $0x2d3e,%esi
  129790:	lea    0x780d1(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  129797:	lea    0x8db92(%rip),%rcx        # 1b7330 <dst.25588.0.0.384+0x1b30>
  12979e:	xor    %eax,%eax
  1297a0:	callq  159a0 <ggml_abort@plt>
  1297a5:	lea    0x8c2d4(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  1297ac:	mov    $0x2d3d,%esi
  1297b1:	lea    0x780b0(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  1297b8:	lea    0x8db85(%rip),%rcx        # 1b7344 <dst.25588.0.0.384+0x1b44>
  1297bf:	xor    %eax,%eax
  1297c1:	callq  159a0 <ggml_abort@plt>
  1297c6:	lea    0x8c2b3(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  1297cd:	mov    $0x2d3c,%esi
  1297d2:	lea    0x7808f(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  1297d9:	lea    0x8db80(%rip),%rcx        # 1b7360 <dst.25588.0.0.384+0x1b60>
  1297e0:	xor    %eax,%eax
  1297e2:	callq  159a0 <ggml_abort@plt>
  1297e7:	lea    0x8c292(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  1297ee:	mov    $0x2d3b,%esi
  1297f3:	lea    0x7806e(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  1297fa:	lea    0x8d94f(%rip),%rcx        # 1b7150 <dst.25588.0.0.384+0x1950>
  129801:	xor    %eax,%eax
  129803:	callq  159a0 <ggml_abort@plt>
  129808:	lea    0x8c271(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  12980f:	mov    $0x2d3a,%esi
  129814:	lea    0x7804d(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  12981b:	lea    0x8d946(%rip),%rcx        # 1b7168 <dst.25588.0.0.384+0x1968>
  129822:	xor    %eax,%eax
  129824:	callq  159a0 <ggml_abort@plt>
  129829:	lea    0x8c250(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  129830:	mov    $0x2d39,%esi
  129835:	lea    0x7802c(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  12983c:	lea    0x8da41(%rip),%rcx        # 1b7284 <dst.25588.0.0.384+0x1a84>
  129843:	xor    %eax,%eax
  129845:	callq  159a0 <ggml_abort@plt>
  12984a:	lea    0x8c22f(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  129851:	mov    $0x2d33,%esi
  129856:	lea    0x7800b(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  12985d:	lea    0x8c870(%rip),%rcx        # 1b60d4 <dst.25588.0.0.384+0x8d4>
  129864:	xor    %eax,%eax
  129866:	callq  159a0 <ggml_abort@plt>
  12986b:	lea    0x8c20e(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  129872:	mov    $0x2d32,%esi
  129877:	lea    0x77fea(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  12987e:	lea    0x8daf7(%rip),%rcx        # 1b737c <dst.25588.0.0.384+0x1b7c>
  129885:	xor    %eax,%eax
  129887:	callq  159a0 <ggml_abort@plt>
  12988c:	lea    0x8c1ed(%rip),%rdi        # 1b5a80 <dst.25588.0.0.384+0x280>
  129893:	mov    $0x2d31,%esi
  129898:	lea    0x77fc9(%rip),%rdx        # 1a1868 <il0_peep_printf_format_0+0x2c>
  12989f:	lea    0x8daf2(%rip),%rcx        # 1b7398 <dst.25588.0.0.384+0x1b98>
  1298a6:	xor    %eax,%eax
  1298a8:	callq  159a0 <ggml_abort@plt>
  1298ad:	nopl   (%rax)
