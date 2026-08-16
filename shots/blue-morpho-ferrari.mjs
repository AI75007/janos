/**
 * Shot: Blue Morpho butterfly landing on a red Ferrari at the Grand Canyon.
 * Looping 10s, 16:9, website background plate.
 */

export const shot = {
  id: "blue-morpho-ferrari-canyon",
  duration: 10,
  fps: 24,
  aspectRatio: "16:9",
  resolution: "7680x4320",
  loop: true,
};

export const subject = {
  butterfly:
    "Blue Morpho butterfly, vivid iridescent cobalt-blue wings, dark brown " +
    "to black wing borders, distinct white marginal dots, translucent scales",
  car:
    "sleek red Ferrari sports car, glossy polished clearcoat hood, " +
    "sharp ray-traced reflections",
  location:
    "precipice of a rugged cliff edge overlooking the Grand Canyon",
  background:
    "layered ancient red-orange sandstone formations, deep shadowy gorges, " +
    "hazy sun-drenched horizon stretching to infinity",
};

export const lighting = {
  key: "warm golden-hour sunlight, low angle",
  effects: [
    "dramatic highlights raking across the car's curves",
    "backlit translucency through the butterfly's wings",
    "volumetric light shafts in canyon haze",
  ],
};

export const camera = {
  move: "slow dolly-in",
  lens: "85mm",
  aperture: "T2.0",
  shutter: "1/48",
  focus: "butterfly thorax, car hood within the focal plane",
  depthOfField: "shallow; butterfly and hood sharp, canyon soft",
};

export const beats = [
  {
    t: [0.0, 2.5],
    action: "Butterfly drifts in from frame right, wings beating slow and wide",
    camera: "dolly-in begins, hood along the lower third",
    light: "golden key, canyon haze glowing behind",
  },
  {
    t: [2.5, 4.5],
    action: "Descent over the hood, wings flare to brake, legs extend",
    camera: "dolly continues, butterfly reflection rises to meet it in the paint",
    light: "specular streak sweeps the fender as the angle closes",
  },
  {
    t: [4.5, 5.5],
    action: "Touchdown on the clearcoat, legs settle, wings held open",
    camera: "push slows",
    light: "wing scales catch the sun, cobalt flashes to violet",
  },
  {
    t: [5.5, 8.0],
    action: "Wings fold and open twice, slow, then still",
    camera: "close on butterfly and its mirror image",
    light: "canyon sky reflected across the hood behind the wings",
  },
  {
    t: [8.0, 10.0],
    action: "Wings at rest, faint breeze tremor only",
    camera: "dolly eases out to the opening framing for the loop seam",
    light: "returns to the 0.0s exposure and sun angle",
  },
];

export const technique = [
  "Unreal Engine 5 quality",
  "8k resolution",
  "ray-traced reflections",
  "volumetric lighting",
  "hyper-realistic textures",
  "photorealistic, cinematic",
];

export const negativePrompt = [
  "cartoon", "illustration", "CGI plastic look", "oversaturated", "HDR halos",
  "warped wings", "extra legs", "duplicate butterfly", "morphing wing patterns",
  "wrong wing pattern", "orange wings", "text", "watermark", "logo",
  "fast camera movement", "whip pan", "jump cut", "shaky cam", "motion blur smear",
  "overcast sky", "night", "people", "other vehicles", "guardrail", "road markings",
  "wings clipping through the car body", "flickering", "loop seam pop",
].join(", ");

export const prosePrompt = `
Cinematic photorealistic animation. A Blue Morpho butterfly with vivid,
iridescent cobalt-blue wings, dark brown to black borders and distinct white
dots flutters gracefully into frame and lands delicately on the glossy, polished
hood of a sleek red Ferrari. The car is parked on the precipice of a rugged
cliff edge overlooking the Grand Canyon: layered ancient red-orange sandstone
formations, deep shadowy gorges, and a hazy sun-drenched horizon stretching to
infinity. Warm golden-hour sunlight casts dramatic highlights along the car's
curves and lights the translucent texture of the wings from behind. The wings
flap gently once or twice before settling; the Ferrari's paint holds a sharp
reflection of both the butterfly and the canyon sky. Slow dolly-in, shallow
depth of field with the butterfly and car in sharp focus, ray-traced
reflections, volumetric lighting, hyper-realistic textures, Unreal Engine 5
quality, 8k. Seamless 10-second loop, 16:9.
`.trim().replace(/\s+/g, " ");

const structuredPrompt = [
  `Subject: ${subject.butterfly} landing on the hood of a ${subject.car}`,
  `Location: ${subject.location}`,
  `Background: ${subject.background}`,
  `Camera: ${camera.move}, ${camera.lens} ${camera.aperture}, ${camera.depthOfField}`,
  `Motion: ${beats.map((b) => b.action.toLowerCase()).join("; ")}`,
  `Lighting: ${lighting.key}; ${lighting.effects.join("; ")}`,
  `Style: ${technique.join(", ")}`,
  `Loop: seamless, first and last frame matched`,
  `Camera motion: low`,
].join("\n");

export const payloads = {
  veo: {
    model: "veo-3",
    prompt: prosePrompt,
    negativePrompt,
    durationSeconds: shot.duration,
    aspectRatio: shot.aspectRatio,
    fps: shot.fps,
    personGeneration: "dont_allow",
  },

  sora: {
    model: "sora-2",
    prompt: `${prosePrompt}\n\nAvoid: ${negativePrompt}`,
    seconds: shot.duration,
    size: "1920x1080",
  },

  runway: {
    model: "gen4_turbo",
    promptText: structuredPrompt,
    duration: shot.duration,
    ratio: "1280:720",
    seed: 20260816,
  },

  kling: {
    model_name: "kling-v2-master",
    prompt: structuredPrompt,
    negative_prompt: negativePrompt,
    duration: String(shot.duration),
    aspect_ratio: shot.aspectRatio,
    cfg_scale: 0.5,
    mode: "pro",
  },
};

export function buildPrompt(provider = "veo") {
  const payload = payloads[provider];
  if (!payload) throw new Error(`unknown provider: ${provider}`);
  return payload;
}

export function timeline() {
  return beats.map(({ t, action, camera: cam, light }) => ({
    in: t[0],
    out: t[1],
    frames: Math.round((t[1] - t[0]) * shot.fps),
    action,
    camera: cam,
    light,
  }));
}

export default { shot, subject, camera, lighting, beats, buildPrompt, timeline };
