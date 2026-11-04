import { Composition } from "remotion";
import { MyComposition } from "./Composition";
import { FRAMES_POR_PLANO, ProductoB, ProductoBProps } from "./formatoB/ProductoB";

const porDefecto: ProductoBProps = {
  planos: [],
  musica: "musica/ambient-b.m4a",
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <MyComposition />
      <Composition
        id="ProductoB"
        component={ProductoB}
        fps={30}
        width={1080}
        height={1920}
        durationInFrames={FRAMES_POR_PLANO * 4}
        defaultProps={porDefecto}
        calculateMetadata={({ props }) => ({
          durationInFrames: FRAMES_POR_PLANO * Math.max(props.planos.length, 1),
        })}
      />
    </>
  );
};
