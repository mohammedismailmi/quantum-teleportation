import React, { useMemo } from 'react';
import katex from 'katex';

export default function KatexView({ math, block = false, className = '' }) {
  const html = useMemo(() => {
    if (!math) return '';
    try {
      let cleaned = String(math);
      // Normalize double backslashes before LaTeX command names (e.g. \\mathcal -> \mathcal, \\rho -> \rho)
      cleaned = cleaned.replace(/\\\\([a-zA-Z]+)/g, '\\$1');
      // Normalize quadruple backslashes in matrix row breaks down to double backslashes (\\\\ -> \\)
      cleaned = cleaned.replace(/\\\\\\\\/g, '\\\\');

      return katex.renderToString(cleaned, {
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
