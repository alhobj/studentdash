import React from 'react';
/** Native disclosure menus start closed and retain their state without changing the canvas. */
export function ControlPanel({children}:{children:React.ReactNode}){
 return <aside className="tree-control-panel" aria-label="Tree controls"><h2>Tree controls</h2>{children}</aside>;
}
export function ControlSection({title,children,hidden=false}:{title:string;children:React.ReactNode;hidden?:boolean}){
 return <details className="control-section" hidden={hidden}><summary>{title}</summary><div className="control-section-body">{children}</div></details>;
}
