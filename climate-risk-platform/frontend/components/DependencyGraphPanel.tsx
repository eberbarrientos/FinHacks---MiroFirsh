'use client';

/**
 * DependencyGraphPanel - Visualizes entity dependencies and cascade paths
 * 
 * Uses a force-directed graph layout to show:
 * - Entities as nodes (colored by risk level)
 * - Dependencies as edges
 * - Cascade propagation paths
 */

import React, { useEffect, useRef, useState } from 'react';
import { CascadeEvent } from '@/lib/mirofish-api';

interface DependencyGraphPanelProps {
  cascadeEvents: CascadeEvent[];
  onEntityClick?: (entity: string) => void;
  className?: string;
}

interface GraphNode {
  id: string;
  label: string;
  risk: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

export function DependencyGraphPanel({
  cascadeEvents,
  onEntityClick,
  className = '',
}: DependencyGraphPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [hoveredEntity, setHoveredEntity] = useState<string | null>(null);
  const animationRef = useRef<number>();

  // Build graph from cascade events
  useEffect(() => {
    if (!cascadeEvents || cascadeEvents.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const nodeMap = new Map<string, GraphNode>();
    const edgeList: GraphEdge[] = [];

    // Extract entities and build nodes
    cascadeEvents.forEach((event, index) => {
      const entity = event.entity || event.issuer || `Entity ${index + 1}`;
      const risk = event.loss || event.impact || 0;

      if (!nodeMap.has(entity)) {
        nodeMap.set(entity, {
          id: entity,
          label: entity,
          risk: risk,
          x: Math.random() * 600 + 100,
          y: Math.random() * 400 + 100,
          vx: 0,
          vy: 0,
        });
      } else {
        // Aggregate risk if entity appears multiple times
        const node = nodeMap.get(entity)!;
        node.risk = Math.max(node.risk, risk);
      }
    });

    // Build edges (simplified - connect sequential events)
    for (let i = 0; i < cascadeEvents.length - 1; i++) {
      const source = cascadeEvents[i].entity || cascadeEvents[i].issuer || `Entity ${i + 1}`;
      const target = cascadeEvents[i + 1].entity || cascadeEvents[i + 1].issuer || `Entity ${i + 2}`;
      
      if (source !== target) {
        edgeList.push({
          source,
          target,
          weight: 1,
        });
      }
    }

    setNodes(Array.from(nodeMap.values()));
    setEdges(edgeList);
  }, [cascadeEvents]);

  // Force-directed layout simulation
  useEffect(() => {
    if (nodes.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Physics parameters
    const repulsionStrength = 5000;
    const attractionStrength = 0.01;
    const damping = 0.9;
    const centerStrength = 0.01;

    const simulate = () => {
      // Apply forces
      const updatedNodes = nodes.map(node => ({ ...node }));

      // Repulsion between nodes
      for (let i = 0; i < updatedNodes.length; i++) {
        for (let j = i + 1; j < updatedNodes.length; j++) {
          const dx = updatedNodes[j].x - updatedNodes[i].x;
          const dy = updatedNodes[j].y - updatedNodes[i].y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsionStrength / (distance * distance);

          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          updatedNodes[i].vx -= fx;
          updatedNodes[i].vy -= fy;
          updatedNodes[j].vx += fx;
          updatedNodes[j].vy += fy;
        }
      }

      // Attraction along edges
      edges.forEach(edge => {
        const sourceNode = updatedNodes.find(n => n.id === edge.source);
        const targetNode = updatedNodes.find(n => n.id === edge.target);

        if (sourceNode && targetNode) {
          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = distance * attractionStrength;

          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          sourceNode.vx += fx;
          sourceNode.vy += fy;
          targetNode.vx -= fx;
          targetNode.vy -= fy;
        }
      });

      // Center gravity
      updatedNodes.forEach(node => {
        const dx = width / 2 - node.x;
        const dy = height / 2 - node.y;
        node.vx += dx * centerStrength;
        node.vy += dy * centerStrength;
      });

      // Update positions
      updatedNodes.forEach(node => {
        node.x += node.vx;
        node.y += node.vy;
        node.vx *= damping;
        node.vy *= damping;

        // Boundary constraints
        node.x = Math.max(50, Math.min(width - 50, node.x));
        node.y = Math.max(50, Math.min(height - 50, node.y));
      });

      setNodes(updatedNodes);

      // Render
      ctx.clearRect(0, 0, width, height);

      // Draw edges
      ctx.strokeStyle = 'rgba(100, 200, 255, 0.3)';
      ctx.lineWidth = 1;
      edges.forEach(edge => {
        const sourceNode = updatedNodes.find(n => n.id === edge.source);
        const targetNode = updatedNodes.find(n => n.id === edge.target);

        if (sourceNode && targetNode) {
          ctx.beginPath();
          ctx.moveTo(sourceNode.x, sourceNode.y);
          ctx.lineTo(targetNode.x, targetNode.y);
          ctx.stroke();
        }
      });

      // Draw nodes
      updatedNodes.forEach(node => {
        const isSelected = node.id === selectedEntity;
        const isHovered = node.id === hoveredEntity;
        
        // Determine color based on risk level
        let color = '#10b981'; // green (low risk)
        if (node.risk > 70) {
          color = '#ef4444'; // red (high risk)
        } else if (node.risk > 40) {
          color = '#f59e0b'; // amber (medium risk)
        }

        // Draw node circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, isSelected || isHovered ? 12 : 8, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
        
        if (isSelected || isHovered) {
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Draw label
        if (isSelected || isHovered || updatedNodes.length < 15) {
          ctx.fillStyle = '#ffffff';
          ctx.font = '12px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(node.label.substring(0, 20), node.x, node.y - 15);
        }
      });

      animationRef.current = requestAnimationFrame(simulate);
    };

    simulate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [nodes, edges, selectedEntity, hoveredEntity]);

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find clicked node
    const clickedNode = nodes.find(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      return Math.sqrt(dx * dx + dy * dy) < 12;
    });

    if (clickedNode) {
      setSelectedEntity(clickedNode.id);
      onEntityClick?.(clickedNode.id);
    } else {
      setSelectedEntity(null);
    }
  };

  // Handle canvas hover
  const handleCanvasMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find hovered node
    const hoveredNode = nodes.find(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      return Math.sqrt(dx * dx + dy * dy) < 12;
    });

    setHoveredEntity(hoveredNode?.id || null);
    canvas.style.cursor = hoveredNode ? 'pointer' : 'default';
  };

  if (!cascadeEvents || cascadeEvents.length === 0) {
    return (
      <div className={`rounded-2xl bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 p-8 ${className}`}>
        <h3 className="text-lg font-semibold text-white mb-4">Dependency Graph</h3>
        <div className="flex items-center justify-center h-64 text-slate-400">
          No cascade events to visualize
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-2xl bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Dependency Graph</h3>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-slate-400">Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500"></div>
            <span className="text-slate-400">Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-slate-400">High Risk</span>
          </div>
        </div>
      </div>
      
      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        onClick={handleCanvasClick}
        onMouseMove={handleCanvasMove}
        className="w-full h-auto rounded-xl bg-slate-950/50"
      />
      
      {selectedEntity && (
        <div className="mt-4 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
          <p className="text-sm text-slate-300">
            <span className="font-semibold text-white">Selected:</span> {selectedEntity}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Click on nodes to highlight related cascade events
          </p>
        </div>
      )}
    </div>
  );
}
