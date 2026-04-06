"use client";
import React, { useRef } from "react";
import { useScroll, useTransform, motion, MotionValue } from "framer-motion";

export const ContainerScroll = ({
  titleComponent,
  children,
}: {
  titleComponent: string | React.ReactNode;
  children: React.ReactNode;
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Animate as the container scrolls into view (start end → end end)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end end"],
  });

  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Tilted when entering, flat when fully in view
  const rotate = useTransform(scrollYProgress, [0, 0.65], [18, 0]);
  const scale = useTransform(
    scrollYProgress,
    [0, 0.65],
    isMobile ? [0.82, 1] : [0.88, 1]
  );
  const translate = useTransform(scrollYProgress, [0, 0.65], [0, -50]);

  return (
    <div
      ref={containerRef}
      className="min-h-[120vh] flex flex-col items-center justify-start relative pt-16 pb-10 px-4 md:px-8"
    >
      <div className="w-full relative" style={{ perspective: "1200px" }}>
        <Header translate={translate} titleComponent={titleComponent} />
        <Card rotate={rotate} translate={translate} scale={scale}>
          {children}
        </Card>
      </div>
    </div>
  );
};

export const Header = ({ translate, titleComponent }: any) => {
  return (
    <motion.div
      style={{ translateY: translate }}
      className="w-full mx-auto text-center mb-8"
    >
      {titleComponent}
    </motion.div>
  );
};

export const Card = ({
  rotate,
  scale,
  children,
}: {
  rotate: MotionValue<number>;
  scale: MotionValue<number>;
  translate: MotionValue<number>;
  children: React.ReactNode;
}) => {
  return (
    <motion.div
      style={{
        rotateX: rotate,
        scale,
        transformOrigin: "top center",
        boxShadow:
          "0 0 #0000004d, 0 9px 20px #0000004a, 0 37px 37px #00000042, 0 84px 50px #00000026, 0 149px 60px #0000000a, 0 233px 65px #00000003",
      }}
      className="w-full min-h-[80vh] border-4 border-[#6C6C6C] p-2 md:p-5 bg-[#222222] rounded-[30px] shadow-2xl"
    >
      <div className="h-full w-full min-h-[calc(80vh-2.5rem)] overflow-hidden rounded-2xl bg-zinc-900 md:rounded-2xl md:p-4">
        {children}
      </div>
    </motion.div>
  );
};
