import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';

interface MarkdownProps {
  content: string;
  className?: string;
}

const Markdown: React.FC<MarkdownProps> = ({ content, className = '' }) => {
  return (
    <div className={`article-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        components={{
          // Custom link component to handle external links
          a: ({ href, children, ...props }) => {
            const isExternal = href?.startsWith('http');
            return (
              <a
                href={href}
                {...props}
                {...(isExternal && {
                  target: '_blank',
                  rel: 'noopener noreferrer'
                })}
              >
                {children}
                {isExternal && (
                  <svg
                    className="inline w-3 h-3 ml-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                )}
              </a>
            );
          },
          // Add IDs to headings for table of contents
          h1: ({ children, ...props }) => (
            <h1 id={generateId(children)} {...props}>
              {children}
            </h1>
          ),
          h2: ({ children, ...props }) => (
            <h2 id={generateId(children)} {...props}>
              {children}
            </h2>
          ),
          h3: ({ children, ...props }) => (
            <h3 id={generateId(children)} {...props}>
              {children}
            </h3>
          ),
          h4: ({ children, ...props }) => (
            <h4 id={generateId(children)} {...props}>
              {children}
            </h4>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

// Helper function to generate IDs from heading text
function generateId(children: any): string {
  const text = React.Children.toArray(children).join('');
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export default Markdown;