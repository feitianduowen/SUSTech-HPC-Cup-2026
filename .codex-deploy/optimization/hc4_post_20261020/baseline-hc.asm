
/work/apac2602/qwen38-cpu/llama.cpp/build/bin/libggml-cpu.so:     file format elf64-x86-64


Disassembly of section .text:

0000000000129050 <ggml_compute_forward_dsv4_hc_post>:
  129050:	push   %r12
  129052:	push   %r13
  129054:	push   %r14
  129056:	push   %r15
  129058:	push   %rbx
  129059:	push   %rbp
  12905a:	sub    $0x98,%rsp
  129061:	mov    %rsi,%r10
  129064:	mov    %rdi,%rax
  129067:	mov    0x98(%r10),%r8
  12906e:	cmpl   $0x0,(%r8)
  129072:	jne    12936a <ggml_compute_forward_dsv4_hc_post+0x31a>
  129078:	mov    0xa0(%r10),%rsi
  12907f:	mov    0xa8(%r10),%r9
  129086:	mov    0xb0(%r10),%rbp
  12908d:	cmpl   $0x0,(%rsi)
  129090:	jne    129561 <ggml_compute_forward_dsv4_hc_post+0x511>
  129096:	cmpl   $0x0,(%r9)
  12909a:	jne    129540 <ggml_compute_forward_dsv4_hc_post+0x4f0>
  1290a0:	cmpl   $0x0,(%r10)
  1290a4:	jne    12951f <ggml_compute_forward_dsv4_hc_post+0x4cf>
  1290aa:	mov    0x10(%r8),%rbx
  1290ae:	mov    0x18(%r8),%r14
  1290b2:	mov    0x18(%rsi),%rcx
  1290b6:	cmp    0x10(%r10),%rbx
  1290ba:	jne    1294fe <ggml_compute_forward_dsv4_hc_post+0x4ae>
  1290c0:	cmp    0x18(%r10),%rcx
  1290c4:	jne    1294dd <ggml_compute_forward_dsv4_hc_post+0x48d>
  1290ca:	cmp    0x20(%r10),%r14
  1290ce:	jne    1294bc <ggml_compute_forward_dsv4_hc_post+0x46c>
  1290d4:	cmp    0x10(%rsi),%rbx
  1290d8:	jne    12949b <ggml_compute_forward_dsv4_hc_post+0x44b>
  1290de:	cmp    0x20(%rsi),%r14
  1290e2:	jne    12947a <ggml_compute_forward_dsv4_hc_post+0x42a>
  1290e8:	cmp    0x10(%r9),%rcx
  1290ec:	jne    129459 <ggml_compute_forward_dsv4_hc_post+0x409>
  1290f2:	cmp    0x18(%r9),%r14
  1290f6:	jne    129438 <ggml_compute_forward_dsv4_hc_post+0x3e8>
  1290fc:	xor    %r13d,%r13d
  1290ff:	xor    %r12d,%r12d
  129102:	xor    %r11d,%r11d
  129105:	test   %rbp,%rbp
  129108:	je     12913e <ggml_compute_forward_dsv4_hc_post+0xee>
  12910a:	cmpl   $0x0,0x0(%rbp)
  12910e:	jne    129417 <ggml_compute_forward_dsv4_hc_post+0x3c7>
  129114:	cmp    0x10(%rbp),%rcx
  129118:	jne    1293f6 <ggml_compute_forward_dsv4_hc_post+0x3a6>
  12911e:	cmp    0x18(%rbp),%rcx
  129122:	jne    1293d5 <ggml_compute_forward_dsv4_hc_post+0x385>
  129128:	cmp    0x20(%rbp),%r14
  12912c:	jne    1293b4 <ggml_compute_forward_dsv4_hc_post+0x364>
  129132:	mov    0x30(%rbp),%r13
  129136:	mov    0x38(%rbp),%r12
  12913a:	mov    0x40(%rbp),%r11
  12913e:	mov    0x30(%r8),%rdx
  129142:	mov    0x38(%r8),%rdi
  129146:	mov    0x30(%rsi),%r15
  12914a:	mov    %rdx,0x58(%rsp)
  12914f:	mov    %rdi,0x50(%rsp)
  129154:	mov    %r15,0x28(%rsp)
  129159:	test   %rsi,%rsi
  12915c:	je     129172 <ggml_compute_forward_dsv4_hc_post+0x122>
  12915e:	mov    0x38(%rsi),%rdx
  129162:	mov    0x40(%rsi),%rdi
  129166:	mov    %rdx,0x30(%rsp)
  12916b:	mov    %rdi,0x20(%rsp)
  129170:	jmp    12917e <ggml_compute_forward_dsv4_hc_post+0x12e>
  129172:	xor    %edx,%edx
  129174:	mov    %rdx,0x30(%rsp)
  129179:	mov    %rdx,0x20(%rsp)
  12917e:	test   %r9,%r9
  129181:	je     129197 <ggml_compute_forward_dsv4_hc_post+0x147>
  129183:	mov    0x30(%r9),%rdx
  129187:	mov    0x38(%r9),%rdi
  12918b:	mov    %rdx,0x60(%rsp)
  129190:	mov    %rdi,0x48(%rsp)
  129195:	jmp    1291a3 <ggml_compute_forward_dsv4_hc_post+0x153>
  129197:	xor    %edx,%edx
  129199:	mov    %rdx,0x60(%rsp)
  12919e:	mov    %rdx,0x48(%rsp)
  1291a3:	test   %r10,%r10
  1291a6:	je     1291cb <ggml_compute_forward_dsv4_hc_post+0x17b>
  1291a8:	mov    0x30(%r10),%rdx
  1291ac:	mov    0x38(%r10),%rdi
  1291b0:	mov    0x40(%r10),%r15
  1291b4:	mov    %rdx,0x88(%rsp)
  1291bc:	mov    %rdi,0x80(%rsp)
  1291c4:	mov    %r15,0x78(%rsp)
  1291c9:	jmp    1291e2 <ggml_compute_forward_dsv4_hc_post+0x192>
  1291cb:	xor    %edx,%edx
  1291cd:	mov    %rdx,0x88(%rsp)
  1291d5:	mov    %rdx,0x80(%rsp)
  1291dd:	mov    %rdx,0x78(%rsp)
  1291e2:	imul   %rbx,%r14
  1291e6:	imul   %rcx,%r14
  1291ea:	movslq 0x4(%rax),%r15
  1291ee:	movslq (%rax),%rdi
  1291f1:	lea    -0x1(%r15,%r14,1),%rax
  1291f6:	cqto   
  1291f8:	idiv   %r15
  1291fb:	imul   %rax,%rdi
  1291ff:	add    %rdi,%rax
  129202:	cmp    %r14,%rax
  129205:	cmovl  %rax,%r14
  129209:	cmp    %r14,%rdi
  12920c:	jge    129358 <ggml_compute_forward_dsv4_hc_post+0x308>
  129212:	mov    0xf8(%r8),%r8
  129219:	mov    0xf8(%r9),%rdx
  129220:	mov    0xf8(%r10),%rax
  129227:	mov    %rbx,%r10
  12922a:	imul   %rcx,%r10
  12922e:	mov    %rax,0x68(%rsp)
  129233:	mov    %rdx,0x38(%rsp)
  129238:	mov    %r8,0x40(%rsp)
  12923d:	mov    %r14,0x70(%rsp)
  129242:	mov    %r11,0x10(%rsp)
  129247:	mov    %r12,0x8(%rsp)
  12924c:	mov    %r13,0x18(%rsp)
  129251:	mov    %rdi,%rax
  129254:	cqto   
  129256:	idiv   %rbx
  129259:	mov    %rdx,%r9
  12925c:	cqto   
  12925e:	idiv   %rcx
  129261:	mov    %rdi,%rax
  129264:	mov    %rdx,%r8
  129267:	cqto   
  129269:	idiv   %r10
  12926c:	mov    0x58(%rsp),%r12
  129271:	mov    %rax,%r14
  129274:	imul   %r9,%r12
  129278:	mov    0x60(%rsp),%r15
  12927d:	imul   %r8,%r15
  129281:	mov    0x50(%rsp),%r11
  129286:	imul   %r14,%r11
  12928a:	mov    0x48(%rsp),%r13
  12928f:	imul   %r14,%r13
  129293:	add    0x40(%rsp),%r12
  129298:	add    0x38(%rsp),%r15
  12929d:	vmovss (%r11,%r12,1),%xmm0
  1292a3:	vmulss 0x0(%r13,%r15,1),%xmm0,%xmm0
  1292aa:	test   %rbp,%rbp
  1292ad:	je     129384 <ggml_compute_forward_dsv4_hc_post+0x334>
  1292b3:	xor    %edx,%edx
  1292b5:	xor    %r11d,%r11d
  1292b8:	xor    %r12d,%r12d
  1292bb:	test   %rcx,%rcx
  1292be:	jle    129324 <ggml_compute_forward_dsv4_hc_post+0x2d4>
  1292c0:	mov    %r9,%r13
  1292c3:	mov    %r14,%rax
  1292c6:	imul   0x28(%rsp),%r13
  1292cc:	imul   0x20(%rsp),%rax
  1292d2:	add    %rax,%r13
  1292d5:	mov    %r8,%rax
  1292d8:	mov    %r14,%r15
  1292db:	imul   0x18(%rsp),%rax
  1292e1:	imul   0x10(%rsp),%r15
  1292e7:	add    %r15,%rax
  1292ea:	add    0xf8(%rsi),%r13
  1292f1:	mov    %rsi,(%rsp)
  1292f5:	add    0xf8(%rbp),%rax
  1292fc:	mov    0x30(%rsp),%rsi
  129301:	mov    0x8(%rsp),%r15
  129306:	vmovss (%r12,%rax,1),%xmm1
  12930c:	inc    %rdx
  12930f:	vfmadd231ss (%r11,%r13,1),%xmm1,%xmm0
  129315:	add    %rsi,%r11
  129318:	add    %r15,%r12
  12931b:	cmp    %rcx,%rdx
  12931e:	jl     129306 <ggml_compute_forward_dsv4_hc_post+0x2b6>
  129320:	mov    (%rsp),%rsi
  129324:	imul   0x80(%rsp),%r8
  12932d:	imul   0x78(%rsp),%r14
  129333:	imul   0x88(%rsp),%r9
  12933c:	add    %r14,%r8
  12933f:	inc    %rdi
  129342:	add    0x68(%rsp),%r9
  129347:	vmovss %xmm0,(%r8,%r9,1)
  12934d:	cmp    0x70(%rsp),%rdi
  129352:	jl     129251 <ggml_compute_forward_dsv4_hc_post+0x201>
  129358:	add    $0x98,%rsp
  12935f:	pop    %rbp
  129360:	pop    %rbx
  129361:	pop    %r15
  129363:	pop    %r14
  129365:	pop    %r13
  129367:	pop    %r12
  129369:	retq   
  12936a:	lea    0x8c2cf(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  129371:	mov    $0x2d7b,%esi
  129376:	lea    0x781bb(%rip),%rdx        # 1a1538 <il0_peep_printf_format_0+0x5c>
  12937d:	xor    %eax,%eax
  12937f:	callq  15960 <ggml_abort@plt>
  129384:	mov    %r8,%rdx
  129387:	mov    %r14,%rax
  12938a:	mov    %r9,%r11
  12938d:	imul   0x30(%rsp),%rdx
  129393:	imul   0x20(%rsp),%rax
  129399:	imul   0x28(%rsp),%r11
  12939f:	add    %rax,%rdx
  1293a2:	add    0xf8(%rsi),%r11
  1293a9:	vaddss (%rdx,%r11,1),%xmm0,%xmm0
  1293af:	jmpq   129324 <ggml_compute_forward_dsv4_hc_post+0x2d4>
  1293b4:	lea    0x8c285(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  1293bb:	mov    $0x2d45,%esi
  1293c0:	lea    0x78141(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  1293c7:	lea    0x8d59a(%rip),%rcx        # 1b6968 <dst.25588.0.0.384+0x15a8>
  1293ce:	xor    %eax,%eax
  1293d0:	callq  15960 <ggml_abort@plt>
  1293d5:	lea    0x8c264(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  1293dc:	mov    $0x2d44,%esi
  1293e1:	lea    0x78120(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  1293e8:	lea    0x8d591(%rip),%rcx        # 1b6980 <dst.25588.0.0.384+0x15c0>
  1293ef:	xor    %eax,%eax
  1293f1:	callq  15960 <ggml_abort@plt>
  1293f6:	lea    0x8c243(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  1293fd:	mov    $0x2d43,%esi
  129402:	lea    0x780ff(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  129409:	lea    0x8d584(%rip),%rcx        # 1b6994 <dst.25588.0.0.384+0x15d4>
  129410:	xor    %eax,%eax
  129412:	callq  15960 <ggml_abort@plt>
  129417:	lea    0x8c222(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  12941e:	mov    $0x2d42,%esi
  129423:	lea    0x780de(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  12942a:	lea    0x8d577(%rip),%rcx        # 1b69a8 <dst.25588.0.0.384+0x15e8>
  129431:	xor    %eax,%eax
  129433:	callq  15960 <ggml_abort@plt>
  129438:	lea    0x8c201(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  12943f:	mov    $0x2d3b,%esi
  129444:	lea    0x780bd(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  12944b:	lea    0x8d572(%rip),%rcx        # 1b69c4 <dst.25588.0.0.384+0x1604>
  129452:	xor    %eax,%eax
  129454:	callq  15960 <ggml_abort@plt>
  129459:	lea    0x8c1e0(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  129460:	mov    $0x2d3a,%esi
  129465:	lea    0x7809c(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  12946c:	lea    0x8d569(%rip),%rcx        # 1b69dc <dst.25588.0.0.384+0x161c>
  129473:	xor    %eax,%eax
  129475:	callq  15960 <ggml_abort@plt>
  12947a:	lea    0x8c1bf(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  129481:	mov    $0x2d39,%esi
  129486:	lea    0x7807b(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  12948d:	lea    0x8d55c(%rip),%rcx        # 1b69f0 <dst.25588.0.0.384+0x1630>
  129494:	xor    %eax,%eax
  129496:	callq  15960 <ggml_abort@plt>
  12949b:	lea    0x8c19e(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  1294a2:	mov    $0x2d38,%esi
  1294a7:	lea    0x7805a(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  1294ae:	lea    0x8d557(%rip),%rcx        # 1b6a0c <dst.25588.0.0.384+0x164c>
  1294b5:	xor    %eax,%eax
  1294b7:	callq  15960 <ggml_abort@plt>
  1294bc:	lea    0x8c17d(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  1294c3:	mov    $0x2d37,%esi
  1294c8:	lea    0x78039(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  1294cf:	lea    0x8d326(%rip),%rcx        # 1b67fc <dst.25588.0.0.384+0x143c>
  1294d6:	xor    %eax,%eax
  1294d8:	callq  15960 <ggml_abort@plt>
  1294dd:	lea    0x8c15c(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  1294e4:	mov    $0x2d36,%esi
  1294e9:	lea    0x78018(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  1294f0:	lea    0x8d31d(%rip),%rcx        # 1b6814 <dst.25588.0.0.384+0x1454>
  1294f7:	xor    %eax,%eax
  1294f9:	callq  15960 <ggml_abort@plt>
  1294fe:	lea    0x8c13b(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  129505:	mov    $0x2d35,%esi
  12950a:	lea    0x77ff7(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  129511:	lea    0x8d418(%rip),%rcx        # 1b6930 <dst.25588.0.0.384+0x1570>
  129518:	xor    %eax,%eax
  12951a:	callq  15960 <ggml_abort@plt>
  12951f:	lea    0x8c11a(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  129526:	mov    $0x2d2f,%esi
  12952b:	lea    0x77fd6(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  129532:	lea    0x8c247(%rip),%rcx        # 1b5780 <dst.25588.0.0.384+0x3c0>
  129539:	xor    %eax,%eax
  12953b:	callq  15960 <ggml_abort@plt>
  129540:	lea    0x8c0f9(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  129547:	mov    $0x2d2e,%esi
  12954c:	lea    0x77fb5(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  129553:	lea    0x8d4ce(%rip),%rcx        # 1b6a28 <dst.25588.0.0.384+0x1668>
  12955a:	xor    %eax,%eax
  12955c:	callq  15960 <ggml_abort@plt>
  129561:	lea    0x8c0d8(%rip),%rdi        # 1b5640 <dst.25588.0.0.384+0x280>
  129568:	mov    $0x2d2d,%esi
  12956d:	lea    0x77f94(%rip),%rdx        # 1a1508 <il0_peep_printf_format_0+0x2c>
  129574:	lea    0x8d4c9(%rip),%rcx        # 1b6a44 <dst.25588.0.0.384+0x1684>
  12957b:	xor    %eax,%eax
  12957d:	callq  15960 <ggml_abort@plt>
  129582:	nopl   0x0(%rax)
  129589:	nopl   0x0(%rax)
