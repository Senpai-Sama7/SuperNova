/**
 * Tooltip — Contextual tooltip for UI elements
 * 15.4.1
 */
import React, { useState } from 'react';

interface TooltipProps { text: string; children: React.ReactNode; position?: 'top' | 'bottom' | 'left' | 'right' }

const Tooltip: React.FC<TooltipProps> = ({ text, children, position = 'top' }) => {
  const [show, setShow] = useState(false);
  return (
    <span className="nv-tooltip-wrapper" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}
      style={{ position: 'relative', display: 'inline-block' }}>
      {children}
      {show && <span className={`nv-tooltip nv-tooltip-${position}`} role="tooltip">{text}</span>}
    </span>
  );
};

export default Tooltip;
