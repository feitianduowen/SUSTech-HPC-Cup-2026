
/work/apac2602/qwen38-cpu/optimization/20261020-hc4-post/sources/hc4-post-4340908/build/bin/libggml-cpu.so:     file format elf64-x86-64


Disassembly of section .text:

0000000000129080 <ggml_compute_forward_dsv4_hc_post>:
  129080:	push   %rbp
  129081:	mov    %rsp,%rbp
  129084:	and    $0xffffffffffffffc0,%rsp
  129088:	push   %r12
  12908a:	push   %r13
  12908c:	push   %r14
  12908e:	push   %r15
  129090:	push   %rbx
  129091:	sub    $0x198,%rsp
  129098:	mov    %rsi,%r11
  12909b:	mov    %rdi,%rdx
  12909e:	mov    0x98(%r11),%r13
  1290a5:	cmpl   $0x0,0x0(%r13)
  1290aa:	jne    129412 <ggml_compute_forward_dsv4_hc_post+0x392>
  1290b0:	mov    0xa0(%r11),%rcx
  1290b7:	mov    0xa8(%r11),%r14
  1290be:	mov    0xb0(%r11),%rsi
  1290c5:	cmpl   $0x0,(%rcx)
  1290c8:	jne    12a0b7 <ggml_compute_forward_dsv4_hc_post+0x1037>
  1290ce:	cmpl   $0x0,(%r14)
  1290d2:	jne    12a096 <ggml_compute_forward_dsv4_hc_post+0x1016>
  1290d8:	cmpl   $0x0,(%r11)
  1290dc:	jne    12a075 <ggml_compute_forward_dsv4_hc_post+0xff5>
  1290e2:	mov    0x10(%r13),%r9
  1290e6:	mov    0x18(%r13),%rbx
  1290ea:	mov    0x18(%rcx),%r12
  1290ee:	cmp    0x10(%r11),%r9
  1290f2:	jne    12a054 <ggml_compute_forward_dsv4_hc_post+0xfd4>
  1290f8:	cmp    0x18(%r11),%r12
  1290fc:	jne    12a033 <ggml_compute_forward_dsv4_hc_post+0xfb3>
  129102:	cmp    0x20(%r11),%rbx
  129106:	jne    12a012 <ggml_compute_forward_dsv4_hc_post+0xf92>
  12910c:	cmp    0x10(%rcx),%r9
  129110:	jne    129ff1 <ggml_compute_forward_dsv4_hc_post+0xf71>
  129116:	cmp    0x20(%rcx),%rbx
  12911a:	jne    129fd0 <ggml_compute_forward_dsv4_hc_post+0xf50>
  129120:	cmp    0x10(%r14),%r12
  129124:	jne    129faf <ggml_compute_forward_dsv4_hc_post+0xf2f>
  12912a:	cmp    0x18(%r14),%rbx
  12912e:	jne    129f8e <ggml_compute_forward_dsv4_hc_post+0xf0e>
  129134:	xor    %r8d,%r8d
  129137:	xor    %edi,%edi
  129139:	xor    %eax,%eax
  12913b:	test   %rsi,%rsi
  12913e:	je     129173 <ggml_compute_forward_dsv4_hc_post+0xf3>
  129140:	cmpl   $0x0,(%rsi)
  129143:	jne    129f6d <ggml_compute_forward_dsv4_hc_post+0xeed>
  129149:	cmp    0x10(%rsi),%r12
  12914d:	jne    129f4c <ggml_compute_forward_dsv4_hc_post+0xecc>
  129153:	cmp    0x18(%rsi),%r12
  129157:	jne    129f2b <ggml_compute_forward_dsv4_hc_post+0xeab>
  12915d:	cmp    0x20(%rsi),%rbx
  129161:	jne    129f0a <ggml_compute_forward_dsv4_hc_post+0xe8a>
  129167:	mov    0x30(%rsi),%r8
  12916b:	mov    0x38(%rsi),%rdi
  12916f:	mov    0x40(%rsi),%rax
  129173:	mov    0x30(%r13),%r10
  129177:	mov    %r10,0x20(%rsp)
  12917c:	mov    0x38(%r13),%r15
  129180:	mov    0x30(%rcx),%r10
  129184:	mov    %r15,0x158(%rsp)
  12918c:	mov    %r10,0x8(%rsp)
  129191:	test   %rcx,%rcx
  129194:	je     1291b0 <ggml_compute_forward_dsv4_hc_post+0x130>
  129196:	mov    0x38(%rcx),%r10
  12919a:	mov    0x40(%rcx),%r15
  12919e:	mov    %r10,0x120(%rsp)
  1291a6:	mov    %r15,0x140(%rsp)
  1291ae:	jmp    1291c3 <ggml_compute_forward_dsv4_hc_post+0x143>
  1291b0:	xor    %r10d,%r10d
  1291b3:	mov    %r10,0x120(%rsp)
  1291bb:	mov    %r10,0x140(%rsp)
  1291c3:	test   %r14,%r14
  1291c6:	je     1291e2 <ggml_compute_forward_dsv4_hc_post+0x162>
  1291c8:	mov    0x30(%r14),%r10
  1291cc:	mov    0x38(%r14),%r15
  1291d0:	mov    %r10,0x160(%rsp)
  1291d8:	mov    %r15,0x150(%rsp)
  1291e0:	jmp    1291f5 <ggml_compute_forward_dsv4_hc_post+0x175>
  1291e2:	xor    %r10d,%r10d
  1291e5:	mov    %r10,0x160(%rsp)
  1291ed:	mov    %r10,0x150(%rsp)
  1291f5:	test   %r11,%r11
  1291f8:	je     12921d <ggml_compute_forward_dsv4_hc_post+0x19d>
  1291fa:	mov    0x30(%r11),%r10
  1291fe:	mov    %r10,0x30(%rsp)
  129203:	mov    0x38(%r11),%r15
  129207:	mov    0x40(%r11),%r10
  12920b:	mov    %r15,0x178(%rsp)
  129213:	mov    %r10,0x170(%rsp)
  12921b:	jmp    129235 <ggml_compute_forward_dsv4_hc_post+0x1b5>
  12921d:	xor    %r10d,%r10d
  129220:	mov    %r10,0x30(%rsp)
  129225:	mov    %r10,0x178(%rsp)
  12922d:	mov    %r10,0x170(%rsp)
  129235:	imul   %r9,%rbx
  129239:	imul   %r12,%rbx
  12923d:	movslq 0x4(%rdx),%r15
  129241:	mov    %rax,0x128(%rsp)
  129249:	movslq (%rdx),%r10
  12924c:	lea    -0x1(%r15,%rbx,1),%rax
  129251:	cqto   
  129253:	idiv   %r15
  129256:	imul   %rax,%r10
  12925a:	add    %r10,%rax
  12925d:	cmp    %rbx,%rax
  129260:	cmovl  %rax,%rbx
  129264:	mov    0x128(%rsp),%rax
  12926c:	cmp    $0x4,%r12
  129270:	je     129461 <ggml_compute_forward_dsv4_hc_post+0x3e1>
  129276:	cmp    %rbx,%r10
  129279:	jge    1293fa <ggml_compute_forward_dsv4_hc_post+0x37a>
  12927f:	mov    0xf8(%r13),%rdx
  129286:	mov    0xf8(%r14),%r14
  12928d:	mov    0xf8(%r11),%r13
  129294:	mov    %r9,%r11
  129297:	mov    %rdi,0x130(%rsp)
  12929f:	imul   %r12,%r11
  1292a3:	mov    %r13,0x28(%rsp)
  1292a8:	mov    %r14,0x10(%rsp)
  1292ad:	mov    %rdx,0x18(%rsp)
  1292b2:	mov    %rbx,0x168(%rsp)
  1292ba:	mov    %rax,0x128(%rsp)
  1292c2:	mov    %r8,0x138(%rsp)
  1292ca:	mov    %r9,0x148(%rsp)
  1292d2:	mov    %rcx,(%rsp)
  1292d6:	mov    0x120(%rsp),%rdi
  1292de:	mov    %r10,%rax
  1292e1:	cqto   
  1292e3:	idivq  0x148(%rsp)
  1292eb:	mov    %rdx,%rcx
  1292ee:	cqto   
  1292f0:	idiv   %r12
  1292f3:	mov    %r10,%rax
  1292f6:	mov    %rdx,%rbx
  1292f9:	cqto   
  1292fb:	idiv   %r11
  1292fe:	mov    0x20(%rsp),%r9
  129303:	mov    %rax,%r14
  129306:	imul   %rcx,%r9
  12930a:	mov    0x160(%rsp),%r15
  129312:	imul   %rbx,%r15
  129316:	mov    0x158(%rsp),%r8
  12931e:	imul   %r14,%r8
  129322:	mov    0x150(%rsp),%r13
  12932a:	imul   %r14,%r13
  12932e:	add    0x18(%rsp),%r9
  129333:	add    0x10(%rsp),%r15
  129338:	vmovss (%r8,%r9,1),%xmm0
  12933e:	vmulss 0x0(%r13,%r15,1),%xmm0,%xmm0
  129345:	test   %rsi,%rsi
  129348:	je     12942c <ggml_compute_forward_dsv4_hc_post+0x3ac>
  12934e:	xor    %r8d,%r8d
  129351:	xor    %r9d,%r9d
  129354:	xor    %r13d,%r13d
  129357:	test   %r12,%r12
  12935a:	jle    1293c4 <ggml_compute_forward_dsv4_hc_post+0x344>
  12935c:	mov    %rcx,%rdx
  12935f:	mov    %r14,%rax
  129362:	imul   0x8(%rsp),%rdx
  129368:	imul   0x140(%rsp),%rax
  129371:	mov    (%rsp),%r15
  129375:	add    %rax,%rdx
  129378:	mov    %rbx,%rax
  12937b:	imul   0x138(%rsp),%rax
  129384:	add    0xf8(%r15),%rdx
  12938b:	mov    %r14,%r15
  12938e:	imul   0x128(%rsp),%r15
  129397:	add    %r15,%rax
  12939a:	mov    0x130(%rsp),%r15
  1293a2:	add    0xf8(%rsi),%rax
  1293a9:	vmovss 0x0(%r13,%rax,1),%xmm1
  1293b0:	inc    %r8
  1293b3:	vfmadd231ss (%r9,%rdx,1),%xmm1,%xmm0
  1293b9:	add    %rdi,%r9
  1293bc:	add    %r15,%r13
  1293bf:	cmp    %r12,%r8
  1293c2:	jl     1293a9 <ggml_compute_forward_dsv4_hc_post+0x329>
  1293c4:	imul   0x178(%rsp),%rbx
  1293cd:	imul   0x170(%rsp),%r14
  1293d6:	imul   0x30(%rsp),%rcx
  1293dc:	add    %r14,%rbx
  1293df:	inc    %r10
  1293e2:	add    0x28(%rsp),%rcx
  1293e7:	vmovss %xmm0,(%rbx,%rcx,1)
  1293ec:	cmp    0x168(%rsp),%r10
  1293f4:	jl     1292de <ggml_compute_forward_dsv4_hc_post+0x25e>
  1293fa:	vzeroupper 
  1293fd:	add    $0x198,%rsp
  129404:	pop    %rbx
  129405:	pop    %r15
  129407:	pop    %r14
  129409:	pop    %r13
  12940b:	pop    %r12
  12940d:	mov    %rbp,%rsp
  129410:	pop    %rbp
  129411:	retq   
  129412:	lea    0x8cea7(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129419:	mov    $0x2da6,%esi
  12941e:	lea    0x78c73(%rip),%rdx        # 1a2098 <il0_peep_printf_format_0+0x5c>
  129425:	xor    %eax,%eax
  129427:	callq  15990 <ggml_abort@plt>
  12942c:	mov    %rbx,%r8
  12942f:	mov    %r14,%rdx
  129432:	mov    %rcx,%r9
  129435:	imul   %rdi,%r8
  129439:	imul   0x140(%rsp),%rdx
  129442:	imul   0x8(%rsp),%r9
  129448:	mov    (%rsp),%rax
  12944c:	add    %rdx,%r8
  12944f:	add    0xf8(%rax),%r9
  129456:	vaddss (%r8,%r9,1),%xmm0,%xmm0
  12945c:	jmpq   1293c4 <ggml_compute_forward_dsv4_hc_post+0x344>
  129461:	cmpq   $0x4,0x20(%rsp)
  129467:	jne    129276 <ggml_compute_forward_dsv4_hc_post+0x1f6>
  12946d:	cmpq   $0x4,0x8(%rsp)
  129473:	jne    129276 <ggml_compute_forward_dsv4_hc_post+0x1f6>
  129479:	cmpq   $0x4,0x30(%rsp)
  12947f:	jne    129276 <ggml_compute_forward_dsv4_hc_post+0x1f6>
  129485:	cmp    %rbx,%r10
  129488:	jge    1293fa <ggml_compute_forward_dsv4_hc_post+0x37a>
  12948e:	mov    0xf8(%r13),%r12
  129495:	mov    0xf8(%rcx),%rcx
  12949c:	mov    0x120(%rsp),%r13
  1294a4:	mov    0xf8(%r14),%rdx
  1294ab:	mov    %r12,0x80(%rsp)
  1294b3:	mov    %rdx,0x110(%rsp)
  1294bb:	lea    (%rdi,%rdi,2),%rdx
  1294bf:	mov    0xf8(%r11),%r14
  1294c6:	lea    0x0(%r13,%rcx,1),%r11
  1294cb:	vmovdqu 0x8cced(%rip),%ymm5        # 1b61c0 <dst.25588.0.0.384+0x1c0>
  1294d3:	lea    (%rcx,%r13,2),%r12
  1294d7:	vmovdqu 0x8c821(%rip),%ymm6        # 1b5d00 <__$U16+0x7da>
  1294df:	vmovdqu 0x8c839(%rip),%ymm7        # 1b5d20 <__$U16+0x7fa>
  1294e7:	mov    %rdx,0x100(%rsp)
  1294ef:	lea    0x0(%r13,%r13,2),%r13
  1294f4:	mov    %r14,0x78(%rsp)
  1294f9:	add    %rcx,%r13
  1294fc:	mov    %rbx,0x168(%rsp)
  129504:	mov    %rax,0x128(%rsp)
  12950c:	mov    %rdi,0x130(%rsp)
  129514:	mov    %r8,0x138(%rsp)
  12951c:	mov    %r9,0x148(%rsp)
  129524:	mov    %rsi,0x108(%rsp)
  12952c:	mov    %r10,%rax
  12952f:	cqto   
  129531:	mov    0x148(%rsp),%rdi
  129539:	idiv   %rdi
  12953c:	mov    %rax,%r9
  12953f:	sub    %rdx,%rdi
  129542:	mov    %r9,%r8
  129545:	sar    %r8
  129548:	shr    $0x3e,%r8
  12954c:	add    %r9,%r8
  12954f:	sar    $0x2,%r8
  129553:	mov    0x160(%rsp),%r15
  12955b:	mov    0x150(%rsp),%r14
  129563:	imul   %r8,%r14
  129567:	mov    0x168(%rsp),%rsi
  12956f:	lea    0x0(,%r8,4),%rbx
  129577:	sub    %rbx,%r9
  12957a:	sub    %r10,%rsi
  12957d:	imul   %r9,%r15
  129581:	add    0x110(%rsp),%r15
  129589:	cmp    %rdi,%rsi
  12958c:	cmovl  %rsi,%rdi
  129590:	vmovss (%r14,%r15,1),%xmm4
  129596:	cmpq   $0x0,0x108(%rsp)
  12959f:	je     129abb <ggml_compute_forward_dsv4_hc_post+0xa3b>
  1295a5:	mov    0x138(%rsp),%r15
  1295ad:	imul   %r9,%r15
  1295b1:	mov    0x128(%rsp),%rbx
  1295b9:	imul   %r8,%rbx
  1295bd:	mov    0x108(%rsp),%rax
  1295c5:	mov    0x130(%rsp),%rsi
  1295cd:	mov    0x100(%rsp),%r14
  1295d5:	add    0xf8(%rax),%r15
  1295dc:	add    %rbx,%r15
  1295df:	vmovss (%r15),%xmm2
  1295e4:	vmovss (%r15,%rsi,1),%xmm1
  1295ea:	vmovss (%r15,%rsi,2),%xmm3
  1295f0:	vmovss (%r14,%r15,1),%xmm0
  1295f6:	test   %rdi,%rdi
  1295f9:	jle    129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  1295ff:	mov    0x158(%rsp),%rax
  129607:	lea    0x0(,%rdi,4),%r15
  12960f:	mov    0x170(%rsp),%rsi
  129617:	imul   0x178(%rsp),%r9
  129620:	imul   %r8,%rax
  129624:	imul   %r8,%rsi
  129628:	mov    0x80(%rsp),%rbx
  129630:	mov    0x78(%rsp),%r14
  129635:	mov    %rsi,0x118(%rsp)
  12963d:	mov    %r15,0x8(%rsp)
  129642:	lea    (%rbx,%rdx,4),%rbx
  129646:	add    %rax,%rbx
  129649:	lea    (%r14,%rdx,4),%rax
  12964d:	lea    (%r9,%rsi,1),%r14
  129651:	add    %rax,%r14
  129654:	mov    %r14,%rsi
  129657:	sub    %rbx,%rsi
  12965a:	cmp    %r15,%rsi
  12965d:	jge    12966d <ggml_compute_forward_dsv4_hc_post+0x5ed>
  12965f:	neg    %rsi
  129662:	cmp    0x8(%rsp),%rsi
  129667:	jl     129a2f <ggml_compute_forward_dsv4_hc_post+0x9af>
  12966d:	imul   0x140(%rsp),%r8
  129676:	mov    0x120(%rsp),%r15
  12967e:	lea    (%r8,%rdx,4),%rsi
  129682:	add    %r11,%rsi
  129685:	neg    %rsi
  129688:	add    %r14,%rsi
  12968b:	add    %r15,%r15
  12968e:	mov    %r15,(%rsp)
  129692:	lea    (%r15,%rdi,4),%r15
  129696:	cmp    %r15,%rsi
  129699:	jge    1296b0 <ggml_compute_forward_dsv4_hc_post+0x630>
  12969b:	mov    0x8(%rsp),%r15
  1296a0:	neg    %rsi
  1296a3:	sub    (%rsp),%r15
  1296a7:	cmp    %r15,%rsi
  1296aa:	jl     129a38 <ggml_compute_forward_dsv4_hc_post+0x9b8>
  1296b0:	cmp    $0x8,%rdi
  1296b4:	jl     129ab4 <ggml_compute_forward_dsv4_hc_post+0xa34>
  1296ba:	cmp    $0x155,%rdi
  1296c1:	jl     129efb <ggml_compute_forward_dsv4_hc_post+0xe7b>
  1296c7:	and    $0x1f,%r14
  1296cb:	test   $0x3,%r14
  1296d2:	je     1296d9 <ggml_compute_forward_dsv4_hc_post+0x659>
  1296d4:	xor    %r14d,%r14d
  1296d7:	jmp    1296f0 <ggml_compute_forward_dsv4_hc_post+0x670>
  1296d9:	test   %r14,%r14
  1296dc:	je     1296f0 <ggml_compute_forward_dsv4_hc_post+0x670>
  1296de:	neg    %r14
  1296e1:	add    $0x20,%r14
  1296e5:	shr    $0x2,%r14
  1296e9:	cmp    %r14,%rdi
  1296ec:	cmovl  %rdi,%r14
  1296f0:	mov    %rdi,%rsi
  1296f3:	sub    %r14,%rsi
  1296f6:	and    $0x7,%rsi
  1296fa:	neg    %rsi
  1296fd:	add    %rdi,%rsi
  129700:	cmp    $0x1,%r14
  129704:	jb     12987b <ggml_compute_forward_dsv4_hc_post+0x7fb>
  12970a:	movq   $0x0,0xb0(%rsp)
  129716:	lea    (%rcx,%rdx,4),%r15
  12971a:	add    %r8,%r15
  12971d:	mov    %r15,0xc0(%rsp)
  129725:	lea    (%rax,%r9,1),%r15
  129729:	add    0x118(%rsp),%r15
  129731:	mov    %r15,0xc8(%rsp)
  129739:	lea    (%r11,%rdx,4),%r15
  12973d:	add    %r8,%r15
  129740:	mov    %r15,0xf0(%rsp)
  129748:	lea    (%r12,%rdx,4),%r15
  12974c:	add    %r8,%r15
  12974f:	mov    %r15,0xe8(%rsp)
  129757:	lea    0x0(%r13,%rdx,4),%r15
  12975c:	add    %r8,%r15
  12975f:	mov    %r13,0x98(%rsp)
  129767:	mov    %r12,0xa0(%rsp)
  12976f:	mov    %r11,0xa8(%rsp)
  129777:	mov    %rcx,0x88(%rsp)
  12977f:	mov    %r10,0x90(%rsp)
  129787:	vmovdqa %ymm6,%ymm15
  12978b:	vmovdqa %ymm7,%ymm14
  12978f:	vbroadcastss %xmm4,%ymm13
  129794:	vbroadcastss %xmm2,%ymm11
  129799:	vbroadcastss %xmm1,%ymm10
  12979e:	vbroadcastss %xmm3,%ymm9
  1297a3:	vbroadcastss %xmm0,%ymm8
  1297a8:	vpbroadcastq %r14,%ymm12
  1297ae:	mov    %r15,%rcx
  1297b1:	mov    0xe8(%rsp),%r10
  1297b9:	mov    0xf0(%rsp),%r11
  1297c1:	mov    0xc8(%rsp),%r12
  1297c9:	mov    0xc0(%rsp),%r13
  1297d1:	mov    0xb0(%rsp),%r15
  1297d9:	nopl   0x0(%rax)
  1297e0:	vpcmpgtq %ymm14,%ymm12,%k0
  1297e6:	vpcmpgtq %ymm15,%ymm12,%k1
  1297ec:	vpaddq %ymm5,%ymm15,%ymm15
  1297f0:	vpaddq %ymm5,%ymm14,%ymm14
  1297f4:	kshiftlw $0x4,%k0,%k2
  1297fa:	korw   %k2,%k1,%k3
  1297fe:	vmovups 0x0(%r13,%r15,4),%ymm16{%k3}{z}
  129806:	vmovups (%rbx,%r15,4),%ymm17{%k3}{z}
  12980d:	vmovups (%r11,%r15,4),%ymm18{%k3}{z}
  129814:	vmovups (%r10,%r15,4),%ymm19{%k3}{z}
  12981b:	vmulps %ymm11,%ymm16,%ymm20
  129821:	vfmadd231ps %ymm17,%ymm13,%ymm20
  129827:	vfmadd231ps %ymm18,%ymm10,%ymm20
  12982d:	vfmadd231ps %ymm19,%ymm9,%ymm20
  129833:	vfmadd231ps (%rcx,%r15,4),%ymm8,%ymm20{%k3}{z}
  12983a:	vmovups %ymm20,(%r12,%r15,4){%k3}
  129841:	add    $0x8,%r15
  129845:	cmp    %r14,%r15
  129848:	jb     1297e0 <ggml_compute_forward_dsv4_hc_post+0x760>
  12984a:	mov    0x98(%rsp),%r13
  129852:	mov    0xa0(%rsp),%r12
  12985a:	mov    0xa8(%rsp),%r11
  129862:	mov    0x88(%rsp),%rcx
  12986a:	mov    0x90(%rsp),%r10
  129872:	cmp    %r14,%rdi
  129875:	je     129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  12987b:	lea    0x8(%r14),%r15
  12987f:	cmp    %r15,%rsi
  129882:	jl     12997a <ggml_compute_forward_dsv4_hc_post+0x8fa>
  129888:	mov    %r12,0xa0(%rsp)
  129890:	lea    (%rcx,%rdx,4),%r15
  129894:	add    %r8,%r15
  129897:	mov    %r15,0xb8(%rsp)
  12989f:	lea    (%rax,%r9,1),%r15
  1298a3:	add    0x118(%rsp),%r15
  1298ab:	mov    %r15,0xd8(%rsp)
  1298b3:	lea    (%r11,%rdx,4),%r15
  1298b7:	add    %r8,%r15
  1298ba:	mov    %r15,0xf8(%rsp)
  1298c2:	lea    (%r12,%rdx,4),%r15
  1298c6:	add    %r8,%r15
  1298c9:	mov    %r15,0xd0(%rsp)
  1298d1:	lea    0x0(%r13,%rdx,4),%r15
  1298d6:	add    %r8,%r15
  1298d9:	mov    %r11,0xa8(%rsp)
  1298e1:	mov    %rcx,0x88(%rsp)
  1298e9:	mov    %r10,0x90(%rsp)
  1298f1:	vbroadcastss %xmm4,%ymm12
  1298f6:	vbroadcastss %xmm2,%ymm11
  1298fb:	vbroadcastss %xmm1,%ymm10
  129900:	vbroadcastss %xmm3,%ymm9
  129905:	vbroadcastss %xmm0,%ymm8
  12990a:	mov    %r15,%rcx
  12990d:	mov    0xd0(%rsp),%r10
  129915:	mov    0xf8(%rsp),%r11
  12991d:	mov    0xd8(%rsp),%r12
  129925:	mov    0xb8(%rsp),%r15
  12992d:	vmulps (%r15,%r14,4),%ymm11,%ymm13
  129933:	vfmadd231ps (%rbx,%r14,4),%ymm12,%ymm13
  129939:	vfmadd231ps (%r11,%r14,4),%ymm10,%ymm13
  12993f:	vfmadd231ps (%r10,%r14,4),%ymm9,%ymm13
  129945:	vfmadd231ps (%rcx,%r14,4),%ymm8,%ymm13
  12994b:	vmovups %ymm13,(%r12,%r14,4)
  129951:	add    $0x8,%r14
  129955:	cmp    %rsi,%r14
  129958:	jb     12992d <ggml_compute_forward_dsv4_hc_post+0x8ad>
  12995a:	mov    0xa0(%rsp),%r12
  129962:	mov    0xa8(%rsp),%r11
  12996a:	mov    0x88(%rsp),%rcx
  129972:	mov    0x90(%rsp),%r10
  12997a:	lea    0x1(%rsi),%r14
  12997e:	cmp    %rdi,%r14
  129981:	ja     129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129987:	add    %r9,%rax
  12998a:	mov    %rdi,%r9
  12998d:	sub    %rsi,%r9
  129990:	lea    (%r11,%rdx,4),%r14
  129994:	vpbroadcastq %r9,%ymm8
  12999a:	add    %r8,%r14
  12999d:	vbroadcastss %xmm2,%ymm10
  1299a2:	vbroadcastss %xmm4,%ymm11
  1299a7:	vbroadcastss %xmm1,%ymm13
  1299ac:	vbroadcastss %xmm3,%ymm15
  1299b1:	vbroadcastss %xmm0,%ymm17
  1299b7:	vpcmpgtq %ymm7,%ymm8,%k0
  1299bd:	vpcmpgtq %ymm6,%ymm8,%k1
  1299c3:	kshiftlw $0x4,%k0,%k2
  1299c9:	korw   %k2,%k1,%k3
  1299cd:	lea    (%r12,%rdx,4),%r15
  1299d1:	vmovups (%rbx,%rsi,4),%ymm12{%k3}{z}
  1299d8:	lea    (%rcx,%rdx,4),%rbx
  1299dc:	vmovups (%r14,%rsi,4),%ymm14{%k3}{z}
  1299e3:	add    %r8,%rbx
  1299e6:	add    %r8,%r15
  1299e9:	add    0x118(%rsp),%rax
  1299f1:	lea    0x0(%r13,%rdx,4),%rdx
  1299f6:	add    %r8,%rdx
  1299f9:	vmovups (%rbx,%rsi,4),%ymm9{%k3}{z}
  129a00:	vmovups (%r15,%rsi,4),%ymm16{%k3}{z}
  129a07:	vmulps %ymm10,%ymm9,%ymm18
  129a0d:	vfmadd231ps %ymm12,%ymm11,%ymm18
  129a13:	vfmadd231ps %ymm14,%ymm13,%ymm18
  129a19:	vfmadd231ps %ymm16,%ymm15,%ymm18
  129a1f:	vfmadd231ps (%rdx,%rsi,4),%ymm17,%ymm18{%k3}{z}
  129a26:	vmovups %ymm18,(%rax,%rsi,4){%k3}
  129a2d:	jmp    129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129a2f:	imul   0x140(%rsp),%r8
  129a38:	movq   $0x0,0xe0(%rsp)
  129a44:	add    %r9,%rax
  129a47:	add    0x118(%rsp),%rax
  129a4f:	lea    (%rcx,%rdx,4),%rsi
  129a53:	add    %r8,%rsi
  129a56:	lea    (%r11,%rdx,4),%r9
  129a5a:	add    %r8,%r9
  129a5d:	lea    (%r12,%rdx,4),%r14
  129a61:	add    %r8,%r14
  129a64:	lea    0x0(%r13,%rdx,4),%rdx
  129a69:	add    %rdx,%r8
  129a6c:	mov    0xe0(%rsp),%rdx
  129a74:	vmulss (%rbx,%rdx,4),%xmm4,%xmm8
  129a79:	vfmadd231ss (%rsi,%rdx,4),%xmm2,%xmm8
  129a7f:	vfmadd231ss (%r9,%rdx,4),%xmm1,%xmm8
  129a85:	vfmadd231ss (%r14,%rdx,4),%xmm3,%xmm8
  129a8b:	vfmadd231ss (%r8,%rdx,4),%xmm0,%xmm8
  129a91:	vmovss %xmm8,(%rax,%rdx,4)
  129a96:	inc    %rdx
  129a99:	cmp    %rdi,%rdx
  129a9c:	jb     129a74 <ggml_compute_forward_dsv4_hc_post+0x9f4>
  129a9e:	add    %rdi,%r10
  129aa1:	cmp    0x168(%rsp),%r10
  129aa9:	jl     12952c <ggml_compute_forward_dsv4_hc_post+0x4ac>
  129aaf:	jmpq   1293fa <ggml_compute_forward_dsv4_hc_post+0x37a>
  129ab4:	xor    %esi,%esi
  129ab6:	jmpq   12997a <ggml_compute_forward_dsv4_hc_post+0x8fa>
  129abb:	test   %rdi,%rdi
  129abe:	jle    129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129ac0:	cmp    $0x6,%rdi
  129ac4:	jle    129d27 <ggml_compute_forward_dsv4_hc_post+0xca7>
  129aca:	mov    0x120(%rsp),%rax
  129ad2:	lea    (%rcx,%rdx,4),%r14
  129ad6:	mov    0x140(%rsp),%rbx
  129ade:	imul   %r9,%rax
  129ae2:	imul   %r8,%rbx
  129ae6:	mov    %rbx,0x70(%rsp)
  129aeb:	lea    (%rax,%rbx,1),%r15
  129aef:	mov    0x78(%rsp),%rbx
  129af4:	add    %r14,%r15
  129af7:	mov    %r14,0x50(%rsp)
  129afc:	mov    0x170(%rsp),%r14
  129b04:	imul   %r8,%r14
  129b08:	mov    %r14,0x18(%rsp)
  129b0d:	lea    (%rbx,%rdx,4),%rsi
  129b11:	mov    0x178(%rsp),%rbx
  129b19:	imul   %r9,%rbx
  129b1d:	mov    %rsi,0x58(%rsp)
  129b22:	add    %rbx,%r14
  129b25:	add    %rsi,%r14
  129b28:	lea    0x0(,%rdi,4),%rsi
  129b30:	mov    %r14,0x28(%rsp)
  129b35:	sub    %r15,%r14
  129b38:	mov    %rsi,0x10(%rsp)
  129b3d:	mov    %r15,0x20(%rsp)
  129b42:	cmp    %rsi,%r14
  129b45:	mov    0x18(%rsp),%rsi
  129b4a:	jge    129b5a <ggml_compute_forward_dsv4_hc_post+0xada>
  129b4c:	neg    %r14
  129b4f:	cmp    0x10(%rsp),%r14
  129b54:	jl     129d27 <ggml_compute_forward_dsv4_hc_post+0xca7>
  129b5a:	mov    0x80(%rsp),%r15
  129b62:	lea    (%r15,%rdx,4),%r14
  129b66:	mov    0x158(%rsp),%r15
  129b6e:	imul   %r8,%r15
  129b72:	add    %r15,%r14
  129b75:	mov    0x28(%rsp),%r15
  129b7a:	sub    %r14,%r15
  129b7d:	mov    %r14,0x30(%rsp)
  129b82:	cmp    0x10(%rsp),%r15
  129b87:	jge    129b97 <ggml_compute_forward_dsv4_hc_post+0xb17>
  129b89:	neg    %r15
  129b8c:	cmp    0x10(%rsp),%r15
  129b91:	jl     129d27 <ggml_compute_forward_dsv4_hc_post+0xca7>
  129b97:	cmp    $0x10,%rdi
  129b9b:	jl     129ebc <ggml_compute_forward_dsv4_hc_post+0xe3c>
  129ba1:	cmp    $0x1d,%rdi
  129ba5:	jl     129ec4 <ggml_compute_forward_dsv4_hc_post+0xe44>
  129bab:	mov    0x28(%rsp),%rdx
  129bb0:	and    $0x1f,%rdx
  129bb4:	je     129bce <ggml_compute_forward_dsv4_hc_post+0xb4e>
  129bb6:	test   $0x3,%rdx
  129bbd:	jne    129ebc <ggml_compute_forward_dsv4_hc_post+0xe3c>
  129bc3:	neg    %rdx
  129bc6:	add    $0x20,%rdx
  129bca:	shr    $0x2,%rdx
  129bce:	lea    0x10(%rdx),%r8
  129bd2:	cmp    %r8,%rdi
  129bd5:	jl     129ebc <ggml_compute_forward_dsv4_hc_post+0xe3c>
  129bdb:	mov    0x50(%rsp),%r8
  129be0:	add    %rax,%r8
  129be3:	add    0x70(%rsp),%r8
  129be8:	mov    %r8,0x50(%rsp)
  129bed:	mov    %rdi,%r8
  129bf0:	sub    %rdx,%r8
  129bf3:	and    $0xf,%r8
  129bf7:	mov    0x58(%rsp),%rax
  129bfc:	neg    %r8
  129bff:	add    %rbx,%rax
  129c02:	add    %rdi,%r8
  129c05:	add    %rsi,%rax
  129c08:	mov    %rax,0x58(%rsp)
  129c0d:	xor    %eax,%eax
  129c0f:	test   %rdx,%rdx
  129c12:	jbe    129c3a <ggml_compute_forward_dsv4_hc_post+0xbba>
  129c14:	mov    0x50(%rsp),%rbx
  129c19:	mov    0x58(%rsp),%rsi
  129c1e:	mov    %r14,%r9
  129c21:	vmovss (%r9,%rax,4),%xmm0
  129c27:	vfmadd213ss (%rbx,%rax,4),%xmm4,%xmm0
  129c2d:	vmovss %xmm0,(%rsi,%rax,4)
  129c32:	inc    %rax
  129c35:	cmp    %rdx,%rax
  129c38:	jb     129c21 <ggml_compute_forward_dsv4_hc_post+0xba1>
  129c3a:	vbroadcastss %xmm4,%ymm0
  129c3f:	mov    0x50(%rsp),%rax
  129c44:	mov    0x58(%rsp),%rbx
  129c49:	mov    0x30(%rsp),%rsi
  129c4e:	mov    0x28(%rsp),%r9
  129c53:	mov    0x20(%rsp),%r14
  129c58:	vmovups (%rsi,%rdx,4),%ymm1
  129c5d:	vmovups 0x20(%rsi,%rdx,4),%ymm2
  129c63:	vfmadd213ps (%rax,%rdx,4),%ymm0,%ymm1
  129c69:	vfmadd213ps 0x20(%r14,%rdx,4),%ymm0,%ymm2
  129c70:	vmovups %ymm1,(%rbx,%rdx,4)
  129c75:	vmovups %ymm2,0x20(%r9,%rdx,4)
  129c7c:	add    $0x10,%rdx
  129c80:	cmp    %r8,%rdx
  129c83:	jb     129c58 <ggml_compute_forward_dsv4_hc_post+0xbd8>
  129c85:	lea    0x1(%r8),%rax
  129c89:	cmp    %rdi,%rax
  129c8c:	ja     129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129c92:	mov    %rdi,%rsi
  129c95:	sub    %r8,%rsi
  129c98:	cmp    $0x4,%rsi
  129c9c:	jl     129ef4 <ggml_compute_forward_dsv4_hc_post+0xe74>
  129ca2:	mov    0x30(%rsp),%rax
  129ca7:	mov    %rsi,%rbx
  129caa:	mov    0x20(%rsp),%r14
  129caf:	and    $0xfffffffffffffffc,%rbx
  129cb3:	mov    0x28(%rsp),%r9
  129cb8:	xor    %edx,%edx
  129cba:	vbroadcastss %xmm4,%xmm0
  129cbf:	lea    (%rax,%r8,4),%rax
  129cc3:	lea    (%r14,%r8,4),%r14
  129cc7:	lea    (%r9,%r8,4),%r9
  129ccb:	vmovups (%rax,%rdx,4),%xmm1
  129cd0:	vfmadd213ps (%r14,%rdx,4),%xmm0,%xmm1
  129cd6:	vmovups %xmm1,(%r9,%rdx,4)
  129cdc:	add    $0x4,%rdx
  129ce0:	cmp    %rbx,%rdx
  129ce3:	jb     129ccb <ggml_compute_forward_dsv4_hc_post+0xc4b>
  129ce5:	cmp    %rsi,%rbx
  129ce8:	jae    129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129cee:	mov    0x30(%rsp),%r9
  129cf3:	mov    0x20(%rsp),%rdx
  129cf8:	mov    0x28(%rsp),%rax
  129cfd:	lea    (%r9,%r8,4),%r9
  129d01:	lea    (%rdx,%r8,4),%rdx
  129d05:	lea    (%rax,%r8,4),%rax
  129d09:	vmovss (%r9,%rbx,4),%xmm0
  129d0f:	vfmadd213ss (%rdx,%rbx,4),%xmm4,%xmm0
  129d15:	vmovss %xmm0,(%rax,%rbx,4)
  129d1a:	inc    %rbx
  129d1d:	cmp    %rsi,%rbx
  129d20:	jb     129d09 <ggml_compute_forward_dsv4_hc_post+0xc89>
  129d22:	jmpq   129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129d27:	mov    %rdi,%rax
  129d2a:	mov    $0x1,%ebx
  129d2f:	movq   $0x0,0x60(%rsp)
  129d38:	shr    %rax
  129d3b:	mov    %rax,0x68(%rsp)
  129d40:	je     129e3c <ggml_compute_forward_dsv4_hc_post+0xdbc>
  129d46:	mov    0x78(%rsp),%rsi
  129d4b:	lea    (%rcx,%rdx,4),%rbx
  129d4f:	mov    0x120(%rsp),%r15
  129d57:	imul   %r9,%r15
  129d5b:	mov    %rcx,0x88(%rsp)
  129d63:	lea    (%rsi,%rdx,4),%rax
  129d67:	mov    0x140(%rsp),%rsi
  129d6f:	imul   %r8,%rsi
  129d73:	mov    %r10,0x90(%rsp)
  129d7b:	lea    (%r15,%rsi,1),%r14
  129d7f:	add    %rbx,%r14
  129d82:	add    %r15,%rbx
  129d85:	mov    %r14,0x38(%rsp)
  129d8a:	add    %rsi,%rbx
  129d8d:	mov    0x178(%rsp),%r14
  129d95:	mov    0x170(%rsp),%rsi
  129d9d:	imul   %r9,%r14
  129da1:	imul   %r8,%rsi
  129da5:	mov    0x158(%rsp),%r15
  129dad:	imul   %r8,%r15
  129db1:	mov    %rbx,0x40(%rsp)
  129db6:	lea    (%r14,%rsi,1),%rbx
  129dba:	add    %rax,%rbx
  129dbd:	add    %r14,%rax
  129dc0:	add    %rsi,%rax
  129dc3:	mov    %rax,0x48(%rsp)
  129dc8:	mov    0x80(%rsp),%rax
  129dd0:	mov    0x48(%rsp),%rcx
  129dd5:	mov    0x40(%rsp),%rsi
  129dda:	mov    0x38(%rsp),%r10
  129ddf:	lea    (%rax,%rdx,4),%rax
  129de3:	mov    0x68(%rsp),%r14
  129de8:	add    %r15,%rax
  129deb:	mov    0x60(%rsp),%r15
  129df0:	vmovss (%rax,%r15,8),%xmm0
  129df6:	vfmadd213ss (%rsi,%r15,8),%xmm4,%xmm0
  129dfc:	vmovss %xmm0,(%rcx,%r15,8)
  129e02:	vmovss 0x4(%rax,%r15,8),%xmm1
  129e09:	vfmadd213ss 0x4(%r10,%r15,8),%xmm4,%xmm1
  129e10:	vmovss %xmm1,0x4(%rbx,%r15,8)
  129e17:	inc    %r15
  129e1a:	cmp    %r14,%r15
  129e1d:	jb     129df0 <ggml_compute_forward_dsv4_hc_post+0xd70>
  129e1f:	mov    %r15,0x60(%rsp)
  129e24:	mov    %r15,%rax
  129e27:	mov    0x88(%rsp),%rcx
  129e2f:	mov    0x90(%rsp),%r10
  129e37:	lea    0x1(%rax,%rax,1),%rbx
  129e3c:	dec    %rbx
  129e3f:	cmp    %rdi,%rbx
  129e42:	jae    129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129e48:	mov    0x80(%rsp),%rsi
  129e50:	lea    (%rcx,%rdx,4),%rax
  129e54:	mov    0x158(%rsp),%r14
  129e5c:	imul   %r8,%r14
  129e60:	lea    (%rsi,%rdx,4),%r15
  129e64:	mov    0x78(%rsp),%rsi
  129e69:	add    %r14,%r15
  129e6c:	lea    (%rsi,%rdx,4),%rsi
  129e70:	mov    0x120(%rsp),%rdx
  129e78:	imul   %r9,%rdx
  129e7c:	imul   0x178(%rsp),%r9
  129e85:	add    %r9,%rsi
  129e88:	add    %rdx,%rax
  129e8b:	mov    0x140(%rsp),%r9
  129e93:	imul   %r8,%r9
  129e97:	imul   0x170(%rsp),%r8
  129ea0:	add    %r9,%rax
  129ea3:	add    %r8,%rsi
  129ea6:	vmovss (%r15,%rbx,4),%xmm0
  129eac:	vfmadd213ss (%rax,%rbx,4),%xmm4,%xmm0
  129eb2:	vmovss %xmm0,(%rsi,%rbx,4)
  129eb7:	jmpq   129a9e <ggml_compute_forward_dsv4_hc_post+0xa1e>
  129ebc:	xor    %r8d,%r8d
  129ebf:	jmpq   129c85 <ggml_compute_forward_dsv4_hc_post+0xc05>
  129ec4:	mov    0x50(%rsp),%rdx
  129ec9:	mov    %rdi,%r8
  129ecc:	add    %rax,%rdx
  129ecf:	and    $0xfffffffffffffff0,%r8
  129ed3:	mov    0x58(%rsp),%rax
  129ed8:	add    %rbx,%rax
  129edb:	add    0x70(%rsp),%rdx
  129ee0:	add    %rsi,%rax
  129ee3:	mov    %rdx,0x50(%rsp)
  129ee8:	xor    %edx,%edx
  129eea:	mov    %rax,0x58(%rsp)
  129eef:	jmpq   129c3a <ggml_compute_forward_dsv4_hc_post+0xbba>
  129ef4:	xor    %ebx,%ebx
  129ef6:	jmpq   129ce5 <ggml_compute_forward_dsv4_hc_post+0xc65>
  129efb:	mov    %rdi,%rsi
  129efe:	xor    %r14d,%r14d
  129f01:	and    $0xfffffffffffffff8,%rsi
  129f05:	jmpq   12987b <ggml_compute_forward_dsv4_hc_post+0x7fb>
  129f0a:	lea    0x8c3af(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129f11:	mov    $0x2d45,%esi
  129f16:	lea    0x7814b(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  129f1d:	lea    0x8dbd8(%rip),%rcx        # 1b7afc <dst.25588.0.0.384+0x1afc>
  129f24:	xor    %eax,%eax
  129f26:	callq  15990 <ggml_abort@plt>
  129f2b:	lea    0x8c38e(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129f32:	mov    $0x2d44,%esi
  129f37:	lea    0x7812a(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  129f3e:	lea    0x8dbcf(%rip),%rcx        # 1b7b14 <dst.25588.0.0.384+0x1b14>
  129f45:	xor    %eax,%eax
  129f47:	callq  15990 <ggml_abort@plt>
  129f4c:	lea    0x8c36d(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129f53:	mov    $0x2d43,%esi
  129f58:	lea    0x78109(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  129f5f:	lea    0x8dbc2(%rip),%rcx        # 1b7b28 <dst.25588.0.0.384+0x1b28>
  129f66:	xor    %eax,%eax
  129f68:	callq  15990 <ggml_abort@plt>
  129f6d:	lea    0x8c34c(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129f74:	mov    $0x2d42,%esi
  129f79:	lea    0x780e8(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  129f80:	lea    0x8dbb5(%rip),%rcx        # 1b7b3c <dst.25588.0.0.384+0x1b3c>
  129f87:	xor    %eax,%eax
  129f89:	callq  15990 <ggml_abort@plt>
  129f8e:	lea    0x8c32b(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129f95:	mov    $0x2d3b,%esi
  129f9a:	lea    0x780c7(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  129fa1:	lea    0x8dbb0(%rip),%rcx        # 1b7b58 <dst.25588.0.0.384+0x1b58>
  129fa8:	xor    %eax,%eax
  129faa:	callq  15990 <ggml_abort@plt>
  129faf:	lea    0x8c30a(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129fb6:	mov    $0x2d3a,%esi
  129fbb:	lea    0x780a6(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  129fc2:	lea    0x8dba7(%rip),%rcx        # 1b7b70 <dst.25588.0.0.384+0x1b70>
  129fc9:	xor    %eax,%eax
  129fcb:	callq  15990 <ggml_abort@plt>
  129fd0:	lea    0x8c2e9(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129fd7:	mov    $0x2d39,%esi
  129fdc:	lea    0x78085(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  129fe3:	lea    0x8db9a(%rip),%rcx        # 1b7b84 <dst.25588.0.0.384+0x1b84>
  129fea:	xor    %eax,%eax
  129fec:	callq  15990 <ggml_abort@plt>
  129ff1:	lea    0x8c2c8(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  129ff8:	mov    $0x2d38,%esi
  129ffd:	lea    0x78064(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  12a004:	lea    0x8db95(%rip),%rcx        # 1b7ba0 <dst.25588.0.0.384+0x1ba0>
  12a00b:	xor    %eax,%eax
  12a00d:	callq  15990 <ggml_abort@plt>
  12a012:	lea    0x8c2a7(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  12a019:	mov    $0x2d37,%esi
  12a01e:	lea    0x78043(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  12a025:	lea    0x8d964(%rip),%rcx        # 1b7990 <dst.25588.0.0.384+0x1990>
  12a02c:	xor    %eax,%eax
  12a02e:	callq  15990 <ggml_abort@plt>
  12a033:	lea    0x8c286(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  12a03a:	mov    $0x2d36,%esi
  12a03f:	lea    0x78022(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  12a046:	lea    0x8d95b(%rip),%rcx        # 1b79a8 <dst.25588.0.0.384+0x19a8>
  12a04d:	xor    %eax,%eax
  12a04f:	callq  15990 <ggml_abort@plt>
  12a054:	lea    0x8c265(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  12a05b:	mov    $0x2d35,%esi
  12a060:	lea    0x78001(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  12a067:	lea    0x8da56(%rip),%rcx        # 1b7ac4 <dst.25588.0.0.384+0x1ac4>
  12a06e:	xor    %eax,%eax
  12a070:	callq  15990 <ggml_abort@plt>
  12a075:	lea    0x8c244(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  12a07c:	mov    $0x2d2f,%esi
  12a081:	lea    0x77fe0(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  12a088:	lea    0x8c885(%rip),%rcx        # 1b6914 <dst.25588.0.0.384+0x914>
  12a08f:	xor    %eax,%eax
  12a091:	callq  15990 <ggml_abort@plt>
  12a096:	lea    0x8c223(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  12a09d:	mov    $0x2d2e,%esi
  12a0a2:	lea    0x77fbf(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  12a0a9:	lea    0x8db0c(%rip),%rcx        # 1b7bbc <dst.25588.0.0.384+0x1bbc>
  12a0b0:	xor    %eax,%eax
  12a0b2:	callq  15990 <ggml_abort@plt>
  12a0b7:	lea    0x8c202(%rip),%rdi        # 1b62c0 <dst.25588.0.0.384+0x2c0>
  12a0be:	mov    $0x2d2d,%esi
  12a0c3:	lea    0x77f9e(%rip),%rdx        # 1a2068 <il0_peep_printf_format_0+0x2c>
  12a0ca:	lea    0x8db07(%rip),%rcx        # 1b7bd8 <dst.25588.0.0.384+0x1bd8>
  12a0d1:	xor    %eax,%eax
  12a0d3:	callq  15990 <ggml_abort@plt>
  12a0d8:	nopl   0x0(%rax,%rax,1)
