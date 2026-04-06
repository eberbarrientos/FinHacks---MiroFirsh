"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowRight, Zap } from "lucide-react";

// ─── Particle Canvas Background ──────────────────────────────────────────────
// Renders as a fixed full-viewport canvas so it persists across all scroll
// sections without any visual breaks.

export const AetherParticleBackground: React.FC = () => {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    const mouse = { x: null as number | null, y: null as number | null, radius: 200 };

    class Particle {
      x: number; y: number;
      directionX: number; directionY: number;
      size: number; color: string;

      constructor(x: number, y: number, dx: number, dy: number, size: number, color: string) {
        this.x = x; this.y = y;
        this.directionX = dx; this.directionY = dy;
        this.size = size; this.color = color;
      }

      draw() {
        ctx!.beginPath();
        ctx!.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
        ctx!.fillStyle = this.color;
        ctx!.fill();
      }

      update() {
        if (this.x > canvas!.width || this.x < 0) this.directionX = -this.directionX;
        if (this.y > canvas!.height || this.y < 0) this.directionY = -this.directionY;

        if (mouse.x !== null && mouse.y !== null) {
          const dx = mouse.x - this.x;
          const dy = mouse.y - this.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius + this.size) {
            const force = (mouse.radius - dist) / mouse.radius;
            this.x -= (dx / dist) * force * 5;
            this.y -= (dy / dist) * force * 5;
          }
        }

        this.x += this.directionX;
        this.y += this.directionY;
        this.draw();
      }
    }

    let particles: Particle[] = [];

    function init() {
      particles = [];
      const count = (canvas!.height * canvas!.width) / 9000;
      for (let i = 0; i < count; i++) {
        const size = Math.random() * 2 + 1;
        const x = Math.random() * (canvas!.width - size * 4) + size * 2;
        const y = Math.random() * (canvas!.height - size * 4) + size * 2;
        particles.push(new Particle(
          x, y,
          (Math.random() * 0.4) - 0.2,
          (Math.random() * 0.4) - 0.2,
          size,
          "rgba(191, 128, 255, 0.8)"
        ));
      }
    }

    function connect() {
      for (let a = 0; a < particles.length; a++) {
        for (let b = a; b < particles.length; b++) {
          const dx = particles[a].x - particles[b].x;
          const dy = particles[a].y - particles[b].y;
          const dist = dx * dx + dy * dy;
          const threshold = (canvas!.width / 7) * (canvas!.height / 7);
          if (dist < threshold) {
            const opacity = 1 - dist / 20000;
            const dxm = particles[a].x - (mouse.x ?? 0);
            const dym = particles[a].y - (mouse.y ?? 0);
            const distMouse = Math.sqrt(dxm * dxm + dym * dym);
            ctx!.strokeStyle = mouse.x && distMouse < mouse.radius
              ? `rgba(255, 255, 255, ${opacity})`
              : `rgba(200, 150, 255, ${opacity})`;
            ctx!.lineWidth = 1;
            ctx!.beginPath();
            ctx!.moveTo(particles[a].x, particles[a].y);
            ctx!.lineTo(particles[b].x, particles[b].y);
            ctx!.stroke();
          }
        }
      }
    }

    function animate() {
      animationFrameId = requestAnimationFrame(animate);
      ctx!.fillStyle = "black";
      ctx!.fillRect(0, 0, canvas!.width, canvas!.height);
      particles.forEach(p => p.update());
      connect();
    }

    function resize() {
      canvas!.width = window.innerWidth;
      canvas!.height = window.innerHeight;
      init();
    }

    const onMouseMove = (e: MouseEvent) => { mouse.x = e.clientX; mouse.y = e.clientY; };
    const onMouseOut = () => { mouse.x = null; mouse.y = null; };

    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseout", onMouseOut);

    resize();
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseout", onMouseOut);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      // fixed so it covers the full page regardless of scroll position
      className="fixed top-0 left-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
};

// ─── Hero Section ─────────────────────────────────────────────────────────────

interface AetherFlowHeroProps {
  trustBadge?: { text: string; icons?: string[] };
  headline?: { line1: string; line2: string };
  subtitle?: string;
  buttons?: {
    primary?: { text: string; onClick?: () => void };
    secondary?: { text: string; onClick?: () => void };
  };
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.2 + 0.5, duration: 0.8, ease: "easeInOut" },
  }),
};

const AetherFlowHero: React.FC<AetherFlowHeroProps> = ({
  trustBadge,
  headline,
  subtitle,
  buttons,
}) => {
  return (
    <div className="relative h-screen w-full flex flex-col items-center justify-center overflow-hidden">
      {/* Overlay content sits above the fixed canvas (z-index 0) */}
      <div className="relative z-10 text-center p-6 max-w-5xl mx-auto">
        {trustBadge && (
          <motion.div
            custom={0} variants={fadeUp} initial="hidden" animate="visible"
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 mb-6 backdrop-blur-sm"
          >
            <Zap className="h-4 w-4 text-purple-400" />
            <span className="text-sm font-medium text-gray-200">{trustBadge.text}</span>
          </motion.div>
        )}

        <motion.h1
          custom={1} variants={fadeUp} initial="hidden" animate="visible"
          className="text-5xl md:text-8xl font-bold tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white to-gray-400"
        >
          {headline?.line1 ?? "Aether Flow"}
          {headline?.line2 && (
            <><br /><span className="text-cyan-400">{headline.line2}</span></>
          )}
        </motion.h1>

        {subtitle && (
          <motion.p
            custom={2} variants={fadeUp} initial="hidden" animate="visible"
            className="max-w-2xl mx-auto text-lg text-gray-400 mb-10"
          >
            {subtitle}
          </motion.p>
        )}

        {buttons && (
          <motion.div
            custom={3} variants={fadeUp} initial="hidden" animate="visible"
            className="flex flex-wrap items-center justify-center gap-4"
          >
            {buttons.primary && (
              <button
                onClick={buttons.primary.onClick}
                className="px-8 py-4 bg-white text-black font-semibold rounded-lg shadow-lg hover:bg-gray-200 transition-colors duration-300 flex items-center gap-2"
              >
                {buttons.primary.text}
                <ArrowRight className="h-5 w-5" />
              </button>
            )}
            {buttons.secondary && (
              <button
                onClick={buttons.secondary.onClick}
                className="px-8 py-4 bg-transparent text-white font-semibold rounded-lg border border-white/20 hover:bg-white/10 transition-colors duration-300"
              >
                {buttons.secondary.text}
              </button>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default AetherFlowHero;
