# Shot: Monarch Butterfly on Ferrari Hood

Cinematic macro. A Monarch lands on the rain-wet hood of a red Ferrari as a
storm rolls in behind it. Single continuous take, no cuts.

---

## Source prompt

> Cinematic macro shot. The Monarch butterfly flies gracefully and gently lands
> on the red Ferrari engine hood. The camera zooms in for an extreme close-up on
> the butterfly and the wet car surface. Background storm clouds move in. A
> lightning bolt flashes. 4K realistic, shallow depth of field.

---

## Beat breakdown (8s)

| Time | Action | Camera | Light |
|---|---|---|---|
| 0.0–2.0s | Butterfly enters frame upper-left, wings beating slow, drifting on air | Wide-ish macro, hood fills lower third | Flat, overcast, cool |
| 2.0–3.5s | Descends, wings flare to brake, legs extend | Slow push begins | Unchanged |
| 3.5–4.5s | Touchdown on wet clearcoat; water beads tremble, reflection meets real wings | Push continues into ECU | Slight dim as clouds thicken |
| 4.5–6.5s | Wings fold and open once, slow. Water bead rolls past the feet | Extreme close-up, wing scales resolve | Ambient falls |
| 6.5–7.2s | Lightning flash — one frame hot, one frame falloff | Locked | Hard blue-white key, hood specular blows out, wings backlit translucent |
| 7.2–8.0s | Return to ambient, wings still. Rain begins to freckle the paint | Holds, breathing handheld drift | Cool, one stop darker than open |

The lightning is the only hard cut in the lighting. Everything else is a slow
continuous fall in exposure — that ramp is what sells the storm's approach more
than the clouds do.

---

## Prompt variants

### Veo / Sora (prose, camera-language forward)

```
Cinematic macro shot, 4K photorealistic. A Monarch butterfly drifts into frame
and lands with delicate precision on the rain-wet hood of a red Ferrari. The
camera pushes slowly into an extreme close-up as the wings settle, water beads
trembling on the glossy clearcoat, the butterfly's orange-and-black wings
mirrored in the paint. Behind, dark storm clouds roll in and the ambient light
falls. A single lightning bolt flashes, backlighting the translucent wings and
igniting a hard specular streak across the hood. Shallow depth of field, macro
lens, natural overcast light turning to storm. Slow, graceful, unhurried.
```

### Runway / Kling (structured, motion-weighted)

```
Subject: Monarch butterfly landing on wet red Ferrari hood
Camera: slow dolly push to extreme close-up, macro lens, shallow DOF
Motion: butterfly descent and landing, wings fold once; storm clouds drift
  behind; water beads on paint
Lighting: overcast falling to storm dark, single lightning flash backlight
Style: photoreal cinematic, 4K, anamorphic, film grain
Camera motion: low
```

### Technical tail (append to any of the above)

```
Shot on 100mm macro, T2.8, 1/48 shutter, 24fps. Focal plane on the butterfly's
thorax. Bokeh circular and creamy. Colour: deep saturated Rosso Corsa red
against cool grey-blue sky. Subtle film grain.
```

---

## Negative prompt

```
cartoon, illustration, CGI plastic look, oversaturated, HDR halos, warped wings,
extra legs, duplicate butterfly, morphing wing patterns, text, watermark, logo,
fast camera movement, whip pan, jump cut, shaky cam, motion blur smear,
dry pavement, sunny sky, flickering, wings clipping through the car body
```

---

## Direction notes

**The landing is the shot.** Most generations rush it. The butterfly should be
airborne for at least a third of the runtime — the flare-and-brake before
touchdown is the moment that reads as "graceful," and it's the first thing a
model will skip if the prompt is crowded. If a take lands the butterfly in the
first second, cut the storm description down rather than adding more landing
language; the model is budgeting motion, and the clouds are stealing it.

**Wet is doing double duty.** The water on the hood gives the paint its mirror
(so you get the butterfly twice) and gives the lightning something to catch. A
dry hood makes the flash land flat. If the model renders the surface dry, push
"rain-beaded", "mirror-wet", "water droplets clinging" ahead of the colour
description — surface state before surface colour.

**Lightning is a lighting event, not a subject.** Prompting the bolt itself
tends to put a fork of lightning in frame, which fights the macro scale. Ask for
the *flash* and its effect — backlit wings, blown specular — and leave the bolt
offscreen. The storm reads better implied.

**Wing anatomy is the failure mode.** Monarchs have a specific pattern (orange
panels, black venation, white-spotted margins) and models drift on it during
wing motion. Prefer takes where the wings are closed or fully open at rest over
takes with more mid-flap frames — and keep the negative prompt's anatomy terms
in, they earn their place.

**Scale conflict.** "Macro" and "Ferrari" pull against each other; the model may
widen out to fit the car in. Never describe the car beyond the hood. The hood is
a red horizon, not a vehicle.

---

## Variations worth shooting

- **Reflection-first** — open on the butterfly's reflection in the paint, rack
  focus up to the real one. Same beats, stronger open.
- **Rain arrival** — first raindrop hits beside the butterfly on the lightning
  beat instead of after it. Tighter, more violent.
- **Wing-only ECU** — skip the landing, open already at rest, single wing fold
  through the flash. Cleanest anatomy, least motion risk.
