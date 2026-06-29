# TTA Transform Inverse Sanity (042)

> 2026-06-29 22:38:22 CST。GT OBB 经 transform forward + inverse 后的 round-trip 几何误差（n=2000 DIOR GT boxes，W=H=1024）。

| transform | round-trip mean IoU | min IoU | center err (px) | angle err (deg) | inverse reliable |
|---|---|---|---|---|---|
| hflip | 1.0000 | 1.0000 | 0.00 | 0.000 | True |
| vflip | 1.0000 | 1.0000 | 0.00 | 0.000 | True |
| rot90 | 1.0000 | 1.0000 | 0.00 | 0.000 | True |

- hflip 逆: cx→W−cx, cy→cy, w→w, h→h, θ→−θ。
- vflip 逆: cx→cx, cy→H−cy, θ→−θ。
- rot90 逆: (cx,cy)→(W−cy,cx) 配 (w,h,θ)→(h,w,θ−90°)（le90）。
- **三 transform inverse 几何均可靠（round-trip IoU=1.0）**。实际 TTA 使用 hflip+vflip（θ→−θ 直接，最稳）；rot90 几何可靠但 near-square 长短边交换在 le90 下对方形目标仍有歧义，作可选。
