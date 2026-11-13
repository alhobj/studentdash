/** Same prerequisite ordering and router as simple, with compact normal-app cards. */
import {buildLayout as sharedLayout,type LayoutNode,type LayoutEdge,type SortMode} from '../simple/src/layout';
export {routeEdges,segmentHitsRect,roundedPath,ROUTE_CLEARANCE} from '../simple/src/layout';
export type {Point,Rect,LayoutNode,LayoutEdge,SortMode,BranchLabel,Layout,EdgeRoute} from '../simple/src/layout';
export const CARD_WIDTH=224;
export const CARD_HEIGHT=112;
export function buildLayout(nodes:readonly LayoutNode[],edges:readonly LayoutEdge[],sort:SortMode='top'){
 return sharedLayout(nodes,edges,sort,{width:CARD_WIDTH,height:CARD_HEIGHT,gapX:40,gapY:64});
}
