"use client";
import React, { useRef } from "react";
import { useScroll, useTransform, motion } from "framer-motion";

/**
 * SectionScroll — scroll-driven parallax without the iPad card wrapper.
 *
 * mode="scroll" (default) — useScroll-driven, works when the section
 *   enters the viewport from outside (landing page sections).
 *
 * mode="inview" — whileInView-driven, works when the content is already
 *   in the DOM but hidden (e.g. inside a tab panel that becomes visible).
 */
export const SectionScroll = ({
  titleComponent,
  children,
  mode = "scroll",
}: {
  titleComponent: React.ReactNode;
  children: React.ReactNode;
  mode?: "scroll" | "inview";
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  const titleY = useTransform(scrollYProgress, [0, 0.4], [60, 0]);
  const titleOpacity = useTransform(scrollYProgress, [0, 0.3], [0, 1]);
  const contentY = useTransform(scrollYProgress, [0.1, 0.5], [80, 0]);
  const contentOpacity = useTransform(scrollYProgress, [0.1, 0.45], [0, 1]);

  if (mode === "inview") {
    return (
      <div ref={containerRef} className="relative w-full">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-5xl mx-auto text-center mb-8"
        >
          {titleComponent}
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.7, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
        >
          {children}
        </motion.div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative w-full">
      <motion.div
        style={{ y: titleY, opacity: titleOpacity }}
        className="max-w-5xl mx-auto text-center mb-16"
      >
        {titleComponent}
      </motion.div>
      <motion.div style={{ y: contentY, opacity: contentOpacity }}>
        {children}
      </motion.div>
    </div>
  );
};
