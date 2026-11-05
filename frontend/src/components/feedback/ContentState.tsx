import type { ReactNode } from "react";
export function ContentState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) { return <div className="content-state"><strong>{title}</strong>{description && <p>{description}</p>}{action}</div> }
