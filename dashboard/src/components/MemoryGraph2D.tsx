/**
 * MemoryGraph2D - 2D Fallback Visualization
 * 
 * Canvas-based 2D visualization for browsers without WebGL support.
 * Maintains visual consistency with the 3D version using similar
 * colors, shapes, and connection styles.
 * 
 * @author Accessibility Engineering Team
 * @phase Phase 4 - 3D Memory Space
 */

import React, { useRef, useEffect, useCallback, useState } from 'react';
import type { MemoryNode } from './MemorySpace3D';
const styles = {
  container: 'memory-graph-2d-container',
  canvas: 'memory-graph-2d-canvas',
  tooltip: 'memory-graph-2d-tooltip',
  tooltipTitle: 'memory-graph-2d-tooltip-title',
  tooltipType: 'memory-graph-2d-tooltip-type'
};

/** Props for MemoryGraph2D */
interface MemoryGraph2DProps {
  memories: MemoryNode[];
  onNodeClick?: (node: MemoryNode) => void;
  onNodeHover?: (node: MemoryNode | null) => void;
  selectedNodeId?: string | null;
  className?: string;
}

/** Memory type visual configuration */
const MEMORY_VISUALS = {
  episodic: {
    color: '#f472b6',
    shape: 'diamond',
    size: 12
  },
  semantic: {
    color: '#fbbf24',
    shape: 'hexagon',
    size: 10
  },
  procedural: {
    color: '#f59e0b',
    shape: 'square',
    size: 14
  }
} as const;

export const MemoryGraph2D: React.FC<MemoryGraph2DProps> = ({
  memories,
  onNodeClick,
  onNodeHover,
  selectedNodeId,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; node: MemoryNode } | null>(null);
  const animationRef = useRef<number>(0);
  const timeRef = useRef(0);

  // Project 3D position to 2D canvas space
  const projectTo2D = useCallback((pos: [number, number, number], canvas: HTMLCanvasElement) => {
    const [x, y, z] = pos;
    const scale = 800 / (800 + z * 50); // Simple perspective projection
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    return {
      x: centerX + x * 40 * scale,
      y: centerY - y * 40 * scale, // Y is inverted in canvas
      scale
    };
  }, []);

  // Draw shape based on type
  const drawShape = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    size: number,
    shape: string,
    color: string,
    pulse: number
  ) => {
    const finalSize = size * (0.9 + pulse * 0.2);
    
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    
    ctx.beginPath();
    
    switch (shape) {
      case 'diamond': // Episodic
        ctx.moveTo(x, y - finalSize);
        ctx.lineTo(x + finalSize * 0.866, y);
        ctx.lineTo(x, y + finalSize);
        ctx.lineTo(x - finalSize * 0.866, y);
        ctx.closePath();
        break;
        
      case 'hexagon': // Semantic
        for (let i = 0; i < 6; i++) {
          const angle = (i * Math.PI) / 3 - Math.PI / 2;
          const px = x + Math.cos(angle) * finalSize;
          const py = y + Math.sin(angle) * finalSize;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        break;
        
      case 'square': // Procedural
        ctx.rect(x - finalSize, y - finalSize, finalSize * 2, finalSize * 2);
        break;
        
      default:
        ctx.arc(x, y, finalSize, 0, Math.PI * 2);
    }
    
    ctx.fill();
    ctx.stroke();
    
    // Glow effect
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, finalSize * 2);
    gradient.addColorStop(0, color + '80'); // 50% opacity
    gradient.addColorStop(1, color + '00'); // 0% opacity
    ctx.fillStyle = gradient;
    ctx.fill();
  };

  // Main render function
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw background gradient
    const bgGradient = ctx.createRadialGradient(
      canvas.width / 2, canvas.height / 2, 0,
      canvas.width / 2, canvas.height / 2, canvas.width
    );
    bgGradient.addColorStop(0, '#1a1a2e');
    bgGradient.addColorStop(1, '#0a0a0f');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Update time for animations
    timeRef.current += 0.016;
    const t = timeRef.current;
    
    // Draw connections first (behind nodes)
    ctx.strokeStyle = '#00ffd5';
    ctx.lineWidth = 1;
    
    memories.forEach(memory => {
      if (memory.relatedIds) {
        memory.relatedIds.forEach(relatedId => {
          const related = memories.find(m => m.id === relatedId);
          if (related && memory.id < related.id) {
            const from = projectTo2D(memory.position, canvas);
            const to = projectTo2D(related.position, canvas);
            
            // Animated pulse along connection
            const pulse = (Math.sin(t * 3 + memory.position[0]) + 1) / 2;
            ctx.globalAlpha = 0.2 + pulse * 0.3;
            
            ctx.beginPath();
            ctx.moveTo(from.x, from.y);
            ctx.lineTo(to.x, to.y);
            ctx.stroke();
          }
        });
      }
    });
    
    ctx.globalAlpha = 1;
    
    // Draw nodes
    memories.forEach(memory => {
      const visual = MEMORY_VISUALS[memory.type];
      const pos = projectTo2D(memory.position, canvas);
      const isHovered = memory.id === hoveredNodeId;
      const isSelected = memory.id === selectedNodeId;
      
      // Pulse animation
      const pulse = (Math.sin(t * 2 + memory.position[0]) + 1) / 2;
      
      // Size multiplier
      const sizeMultiplier = isSelected ? 1.4 : isHovered ? 1.2 : 1;
      const finalSize = visual.size * memory.strength * sizeMultiplier * pos.scale;
      
      // Draw selection ring
      if (isSelected) {
        ctx.strokeStyle = '#00ffd5';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, finalSize * 1.5, 0, Math.PI * 2);
        ctx.stroke();
      }
      
      // Draw node shape
      drawShape(ctx, pos.x, pos.y, finalSize, visual.shape, visual.color, pulse);
      
      // Draw label if hovered or selected
      if (isHovered || isSelected) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(memory.label, pos.x, pos.y + finalSize + 20);
      }
    });
    
    // Schedule next frame
    animationRef.current = requestAnimationFrame(render);
  }, [memories, hoveredNodeId, selectedNodeId, projectTo2D]);

  // Setup canvas and start animation
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    
    // Set canvas size
    const resize = () => {
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    };
    
    resize();
    window.addEventListener('resize', resize);
    
    // Start animation
    render();
    
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationRef.current);
    };
  }, [render]);

  // Handle mouse interactions
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Find hovered node
    let hovered: MemoryNode | null = null;
    
    for (const memory of memories) {
      const pos = projectTo2D(memory.position, canvas);
      const visual = MEMORY_VISUALS[memory.type];
      const size = visual.size * memory.strength * 40; // Scale factor
      
      const dx = mouseX - pos.x;
      const dy = mouseY - pos.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < size) {
        hovered = memory;
        break;
      }
    }
    
    if (hovered) {
      setHoveredNodeId(hovered.id);
      setTooltip({ x: mouseX, y: mouseY - 40, node: hovered });
      onNodeHover?.(hovered);
      canvas.style.cursor = 'pointer';
    } else {
      setHoveredNodeId(null);
      setTooltip(null);
      onNodeHover?.(null);
      canvas.style.cursor = 'default';
    }
  };

  const handleClick = (_e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !hoveredNodeId) return;
    
    const memory = memories.find(m => m.id === hoveredNodeId);
    if (memory) {
      onNodeClick?.(memory);
    }
  };

  const handleMouseLeave = () => {
    setHoveredNodeId(null);
    setTooltip(null);
    onNodeHover?.(null);
  };

  return (
    <div ref={containerRef} className={`${styles.container} ${className}`}>
      <canvas
        ref={canvasRef}
        className={styles.canvas}
        onMouseMove={handleMouseMove}
        onClick={handleClick}
        onMouseLeave={handleMouseLeave}
        style={{ width: '100%', height: '100%' }}
      />
      
      {/* Tooltip */}
      {tooltip && (
        <div
          className={styles.tooltip}
          style={{
            left: tooltip.x,
            top: tooltip.y,
            position: 'absolute'
          }}
        >
          <div className={styles.tooltipTitle}>{tooltip.node.label}</div>
          <div className={styles.tooltipType}>
            {tooltip.node.type} • Strength: {Math.round(tooltip.node.strength * 100)}%
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryGraph2D;
