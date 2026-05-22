import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { markdownComponents } from "./markdownComponents";

type Props = {
  content: string;
};

/** Renders markdown for artifact preview (GFM: tables, task lists, strikethrough). */
export function MarkdownPreview({ content }: Props) {
  return (
    <div className="artifact-md__markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
