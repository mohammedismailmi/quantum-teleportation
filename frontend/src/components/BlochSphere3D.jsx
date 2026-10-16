import React, { useRef, useEffect, useState, useCallback } from 'react';

/**
 * Interactive 3D Bloch Sphere rendered using HTML5 Canvas.
 * Supports mouse/touch rotation, zoom, coordinate axes, latitude/longitude rings,
 * basis state poles, and dynamic statevector arrow.
 */
export default function BlochSphere3D({
  vector = [0, 0, 1], // [x, y, z]
  targetVector = null, // optional second vector for comparison
  title = "Bloch Sphere",
  size = 320,
  showAxes = true,
  showAngles = true,
  interactive = true,
}) {
  const canvasRef = useRef(null);
  const [rotX, setRotX] = useState(0.35); // elevation angle
  const [rotY, setRotY] = useState(0.65); // azimuth angle
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });

  // Mouse / Touch handlers for 3D rotation
  const handleMouseDown = (e) => {
    if (!interactive) return;
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = useCallback((e) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMousePosRef.current.x;
    const dy = e.clientY - lastMousePosRef.current.y;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };

    setRotY((prev) => prev + dx * 0.01);
    setRotX((prev) => Math.max(-Math.PI / 2 + 0.05, Math.min(Math.PI / 2 - 0.05, prev + dy * 0.01)));
  }, []);

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  const handleTouchStart = (e) => {
    if (!interactive || e.touches.length !== 1) return;
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  };

  const handleTouchMove = useCallback((e) => {
    if (!isDraggingRef.current || e.touches.length !== 1) return;
    const dx = e.touches[0].clientX - lastMousePosRef.current.x;
    const dy = e.touches[0].clientY - lastMousePosRef.current.y;
    lastMousePosRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };

    setRotY((prev) => prev + dx * 0.012);
    setRotX((prev) => Math.max(-Math.PI / 2 + 0.05, Math.min(Math.PI / 2 - 0.05, prev + dy * 0.012)));
  }, []);

  useEffect(() => {
    window.addEventListener('mouseup', handleMouseUp);
    return () => window.removeEventListener('mouseup', handleMouseUp);
  }, [handleMouseUp]);

  // Render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const r = (size * 0.36);

    ctx.clearRect(0, 0, size, size);

    // 3D rotation projection functions
    // System: Z is UP, X is FORWARD-RIGHT, Y is DEEP-RIGHT
    const project = (x, y, z) => {
      // Rotate around Z axis (rotY)
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const x1 = x * cosY - y * sinY;
      const y1 = x * sinY + y * cosY;
      const z1 = z;

      // Rotate around horizontal axis (rotX)
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const x2 = x1;
      const y2 = y1 * cosX - z1 * sinX;
      const z2 = y1 * sinX + z1 * cosX;

      // Perspective projection
      const distance = 4.0;
      const fov = distance / (distance - y2 * 0.35);

      return {
        px: cx + x2 * r * fov,
        py: cy - z2 * r * fov,
        depth: y2,
      };
    };

    // Draw sphere background fill with soft white/blue gradient
    const sphereGrad = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 0.1, cx, cy, r);
    sphereGrad.addColorStop(0, '#ffffff');
    sphereGrad.addColorStop(0.85, '#f0f4f9');
    sphereGrad.addColorStop(1, '#dce5f0');

    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = sphereGrad;
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = '#cbd5e1';
    ctx.stroke();

    // Draw latitude circles
    const drawCircle3D = (zVal, strokeStyle, isDashed = false) => {
      const rad = Math.sqrt(Math.max(0, 1 - zVal * zVal));
      ctx.beginPath();
      if (isDashed) ctx.setLineDash([3, 4]);
      else ctx.setLineDash([]);
      ctx.strokeStyle = strokeStyle;
      ctx.lineWidth = 1.0;

      const steps = 64;
      for (let i = 0; i <= steps; i++) {
        const phi = (i / steps) * Math.PI * 2;
        const x = rad * Math.cos(phi);
        const y = rad * Math.sin(phi);
        const p = project(x, y, zVal);
        if (i === 0) ctx.moveTo(p.px, p.py);
        else ctx.lineTo(p.px, p.py);
      }
      ctx.stroke();
      ctx.setLineDash([]);
    };

    // Equator (z = 0)
    drawCircle3D(0, '#94a3b8', false);
    // Latitudes (+0.5, -0.5)
    drawCircle3D(0.5, '#e2e8f0', true);
    drawCircle3D(-0.5, '#e2e8f0', true);

    // Draw Meridian circles (XY planes)
    const drawMeridian = (rotAngle) => {
      ctx.beginPath();
      ctx.setLineDash([2, 4]);
      ctx.strokeStyle = '#e2e8f0';
      ctx.lineWidth = 1.0;
      const steps = 64;
      for (let i = 0; i <= steps; i++) {
        const theta = (i / steps) * Math.PI * 2;
        const x = Math.sin(theta) * Math.cos(rotAngle);
        const y = Math.sin(theta) * Math.sin(rotAngle);
        const z = Math.cos(theta);
        const p = project(x, y, z);
        if (i === 0) ctx.moveTo(p.px, p.py);
        else ctx.lineTo(p.px, p.py);
      }
      ctx.stroke();
      ctx.setLineDash([]);
    };

    drawMeridian(0);
    drawMeridian(Math.PI / 2);

    // Draw Axes (X, Y, Z)
    if (showAxes) {
      const axisLen = 1.25;
      const drawAxis = (pEnd, label, color) => {
        const p0 = project(0, 0, 0);
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.moveTo(p0.px, p0.py);
        ctx.lineTo(pEnd.px, pEnd.py);
        ctx.stroke();

        ctx.fillStyle = color;
        ctx.font = '600 11px Inter, sans-serif';
        ctx.fillText(label, pEnd.px + 4, pEnd.py + 4);
      };

      drawAxis(project(axisLen, 0, 0), '+X (|+)⟩', '#1b468c');
      drawAxis(project(0, axisLen, 0), '+Y (|i)⟩', '#00005d');
      drawAxis(project(0, 0, axisLen), '+Z (|0)⟩', '#0f172a');
      drawAxis(project(0, 0, -axisLen), '-Z (|1)⟩', '#64748b');
    }

    // Poles basis labels
    const drawPoleLabel = (x, y, z, text, align = 'center') => {
      const p = project(x, y, z);
      ctx.fillStyle = '#00005d';
      ctx.font = '600 12px "JetBrains Mono", monospace';
      ctx.textAlign = align;
      ctx.fillText(text, p.px, p.py - 6);

      // Pole dot
      ctx.beginPath();
      ctx.arc(p.px, p.py, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#1b468c';
      ctx.fill();
    };

    drawPoleLabel(0, 0, 1.0, '|0⟩');
    drawPoleLabel(0, 0, -1.0, '|1⟩');
    drawPoleLabel(1.0, 0, 0, '|+⟩');
    drawPoleLabel(-1.0, 0, 0, '|−⟩');

    // Draw Target Vector if comparing
    if (targetVector) {
      const [tx, ty, tz] = targetVector;
      const tp = project(tx, ty, tz);
      const origin = project(0, 0, 0);

      ctx.beginPath();
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = '#059669'; // Emerald green
      ctx.lineWidth = 2.2;
      ctx.moveTo(origin.px, origin.py);
      ctx.lineTo(tp.px, tp.py);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.beginPath();
      ctx.arc(tp.px, tp.py, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#059669';
      ctx.fill();
    }

    // Draw Main State Vector |ψ⟩
    const [vx, vy, vz] = vector || [0, 0, 1];
    const vp = project(vx, vy, vz);
    const origin = project(0, 0, 0);

    // Vector shadow on equator (dashed projection line)
    const equatorProj = project(vx, vy, 0);
    ctx.beginPath();
    ctx.setLineDash([2, 2]);
    ctx.strokeStyle = 'rgba(27, 70, 140, 0.35)';
    ctx.lineWidth = 1;
    ctx.moveTo(origin.px, origin.py);
    ctx.lineTo(equatorProj.px, equatorProj.py);
    ctx.lineTo(vp.px, vp.py);
    ctx.stroke();
    ctx.setLineDash([]);

    // Vector Arrow Body
    ctx.beginPath();
    ctx.strokeStyle = '#1b468c'; // b1 color
    ctx.lineWidth = 3.0;
    ctx.lineCap = 'round';
    ctx.moveTo(origin.px, origin.py);
    ctx.lineTo(vp.px, vp.py);
    ctx.stroke();

    // Vector Arrow Head / Glowing Pointer
    ctx.beginPath();
    ctx.arc(vp.px, vp.py, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#1b468c';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#ffffff';
    ctx.stroke();

    // Glowing outer halo
    ctx.beginPath();
    ctx.arc(vp.px, vp.py, 9, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(27, 70, 140, 0.4)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Vector Label
    ctx.fillStyle = '#00005d';
    ctx.font = '700 12px "JetBrains Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText('|ψ⟩', vp.px + 9, vp.py - 4);
  }, [vector, targetVector, rotX, rotY, size, showAxes, showAngles]);

  // Compute spherical angles
  const [x, y, z] = vector || [0, 0, 1];
  const theta = Math.acos(Math.max(-1, Math.min(1, z)));
  const phi = Math.atan2(y, x);
  const phiNorm = phi < 0 ? phi + 2 * Math.PI : phi;

  return (
    <div className="bloch-container" style={{ width: size, userSelect: 'none' }}>
      <div className="bloch-header">
        <span className="bloch-title">{title}</span>
        {interactive && <span className="bloch-hint">Drag to rotate 3D</span>}
      </div>

      <div
        className="bloch-canvas-wrapper"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        style={{ cursor: interactive ? 'grab' : 'default' }}
      >
        <canvas ref={canvasRef} style={{ width: size, height: size }} />
      </div>

      {showAngles && (
        <div className="bloch-coords">
          <div className="coord-chip">
            <span className="coord-label">x, y, z:</span>
            <span className="coord-val">
              [{x.toFixed(2)}, {y.toFixed(2)}, {z.toFixed(2)}]
            </span>
          </div>
          <div className="coord-chip">
            <span className="coord-label">θ:</span>
            <span className="coord-val">{(theta / Math.PI).toFixed(2)}π</span>
            <span className="coord-label" style={{ marginLeft: 6 }}>φ:</span>
            <span className="coord-val">{(phiNorm / Math.PI).toFixed(2)}π</span>
          </div>
        </div>
      )}
    </div>
  );
}
