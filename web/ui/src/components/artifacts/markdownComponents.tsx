import type { Components } from "react-markdown";

import { MermaidBlock } from "./MermaidBlock";

function codeLanguage(className?: string): string | undefined {
  const match = /language-(\w+)/.exec(className ?? "");
  return match?.[1];
}

export const markdownComponents: Components = {
  code({ className, children, ...props }) {
    const lang = codeLanguage(className);
    const text = String(children).replace(/\n$/, "");

    if (lang === "mermaid") {
      return <MermaidBlock source={text} />;
    }

    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
};
