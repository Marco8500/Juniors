import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Estilo "Formato B" (ver /estilo.md): 4 planos de 92 frames, corte seco,
// un movimiento lento por plano, fondo con degradado de luz y viñeta.
export const FRAMES_POR_PLANO = 92;

export type Movimiento = "push-in" | "pull-out" | "slide-left" | "slide-right" | "fijo";

export type Plano = {
  src: string; // ruta en public/, clip ya graduado con scripts/preparar_clip.sh
  movimiento: Movimiento;
};

export type ProductoBProps = {
  planos: Plano[];
  musica: string;
  framesPorPlano?: number; // por defecto 92; estilo.md actual: 46
  intensidad?: number; // zoom extra a lo largo del plano (0.06 = +6 %)
};

const Movido: React.FC<{ plano: Plano; frames: number; k: number }> = ({ plano, frames, k }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, frames], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.sin),
  });
  let scale = 1.0;
  let x = 0;
  switch (plano.movimiento) {
    case "push-in":
      scale = 1.0 + k * p;
      break;
    case "pull-out":
      scale = 1.0 + k - k * p;
      break;
    case "slide-left":
      scale = 1.04 + k;
      x = 500 * k * (1 - 2 * p);
      break;
    case "slide-right":
      scale = 1.04 + k;
      x = -500 * k * (1 - 2 * p);
      break;
    default:
      scale = 1.02;
  }
  return (
    <AbsoluteFill style={{ transform: `translateX(${x}px) scale(${scale})` }}>
      <OffthreadVideo
        src={staticFile(plano.src)}
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </AbsoluteFill>
  );
};

// Degradado grafito desde arriba (como el fondo de referencia-B) + viñeta 25 %.
const Luz: React.FC = () => (
  <>
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse 90% 55% at 50% 0%, rgba(90,93,98,0.55) 0%, rgba(42,44,48,0.25) 45%, rgba(0,0,0,0) 75%)",
        mixBlendMode: "screen",
      }}
    />
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse 75% 60% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.25) 100%)",
      }}
    />
  </>
);

export const ProductoB: React.FC<ProductoBProps> = ({
  planos,
  musica,
  framesPorPlano = FRAMES_POR_PLANO,
  intensidad = 0.06,
}) => {
  const { durationInFrames } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {planos.map((plano, i) => (
        <Sequence key={i} from={i * framesPorPlano} durationInFrames={framesPorPlano}>
          <Movido plano={plano} frames={framesPorPlano} k={intensidad} />
        </Sequence>
      ))}
      <Luz />
      {musica ? (
        <Audio
          src={staticFile(musica)}
          loop
          volume={(f) =>
            interpolate(f, [durationInFrames - 15, durationInFrames], [1, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          }
        />
      ) : null}
    </AbsoluteFill>
  );
};
