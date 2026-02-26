/**
 * 3D Components Index
 * 
 * Centralized exports for all 3D visualization components.
 * Phase 5: Added adaptive atmosphere components.
 * 
 * @phase Phase 5 - Adaptive Atmosphere
 */

// Core 3D memory space components
export { MemorySpace3D } from '../MemorySpace3D';
export type { MemoryNode, AgentState } from '../MemorySpace3D';

export { MemoryNode3D } from '../MemoryNode3D';
export { MemoryGraph2D } from '../MemoryGraph2D';
export { ConnectionLines3D } from '../ConnectionLines3D';

// Phase 5: Adaptive atmosphere components
export { AdaptiveLighting } from '../AdaptiveLighting';
export { EntropyField, EntropyWave } from '../EntropyField';
export { 
  MemoryNodeAnimator, 
  AnimatedConnection, 
  MemorySpawnEffect,
  MemoryMergeEffect,
  useMemoryAnimations 
} from '../MemoryNodeAnimator';

// Demo component
export { MemorySpace3DDemo } from '../MemorySpace3DDemo';
