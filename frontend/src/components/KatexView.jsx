import React, { useMemo } from 'react';
import katex from 'katex';

export default function KatexView({ math, block = false, className = '' }) {
  const html = useMemo(() => {
    if (!math) return '';
    try {
      return katex.renderToString(math, {
        displayMode: block,
        throwOnError: false,
        output: 'html', // Only generate HTML, preventing duplicate MathML screen reader text
      });
    } catch (err) {
      console.error('KaTeX error:', err);
      return String(math);
    }
  }, [math, block]);

  return (
    <span
      className={`katex-render ${block ? 'katex-block' : 'katex-inline'} ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
