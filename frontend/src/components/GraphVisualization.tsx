import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ZoomIn, ZoomOut, Maximize2, Search } from 'lucide-react'
import { useGraphStore } from '@/store/graphStore'

interface GraphNode extends d3.SimulationNodeDatum {
  id: string
  label: string
  type: string
  size?: number
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode
  target: string | GraphNode
  type: string
}

const nodeColors: Record<string, string> = {
  CONCEPT: '#3b82f6',
  PERSON: '#22c55e',
  ORGANIZATION: '#f59e0b',
  LOCATION: '#ef4444',
  GENE: '#8b5cf6',
  PROTEIN: '#ec4899',
  DISEASE: '#f97316',
  DRUG: '#06b6d4',
  DEFAULT: '#6b7280',
}

export default function GraphVisualization() {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [searchQuery, setSearchQuery] = useState('')
  
  const { nodes, edges, selectedNode, setSelectedNode, fetchGraph } = useGraphStore()

  useEffect(() => {
    fetchGraph()
  }, [fetchGraph])

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || nodes.length === 0) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    // Clear previous SVG content
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height])

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    const g = svg.append('g')

    // Create simulation
    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(edges)
        .id((d) => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30))

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('class', 'graph-link')
      .attr('stroke', '#999')
      .attr('stroke-width', 1.5)

    // Create link labels
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(edges)
      .join('text')
      .attr('class', 'text-xs fill-muted-foreground')
      .attr('text-anchor', 'middle')
      .text((d) => d.type)

    // Create nodes
    const node = g.append('g')
      .selectAll<SVGGElement, GraphNode>('g')
      .data(nodes)
      .join('g')
      .attr('class', 'graph-node')

    // Add drag behavior  
    node.call(d3.drag<SVGGElement, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        }))

    // Add circles to nodes
    node.append('circle')
      .attr('r', (d) => d.size || 8)
      .attr('fill', (d) => nodeColors[d.type] || nodeColors.DEFAULT)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)

    // Add labels to nodes
    node.append('text')
      .attr('x', 12)
      .attr('y', 4)
      .attr('class', 'text-xs fill-foreground')
      .text((d) => d.label)

    // Handle click
    node.on('click', (_, d) => {
      setSelectedNode(d)
    })

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => ((d.source as unknown) as GraphNode).x!)
        .attr('y1', (d) => ((d.source as unknown) as GraphNode).y!)
        .attr('x2', (d) => ((d.target as unknown) as GraphNode).x!)
        .attr('y2', (d) => ((d.target as unknown) as GraphNode).y!)

      linkLabel
        .attr('x', (d) => (((d.source as unknown) as GraphNode).x! + ((d.target as unknown) as GraphNode).x!) / 2)
        .attr('y', (d) => (((d.source as unknown) as GraphNode).y! + ((d.target as unknown) as GraphNode).y!) / 2)

      node.attr('transform', (d) => `translate(${d.x},${d.y})`)
    })

    return () => {
      simulation.stop()
    }
  }, [nodes, edges, setSelectedNode])

  const handleZoomIn = () => {
    if (!svgRef.current) return
    d3.select(svgRef.current).transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      1.5
    )
  }

  const handleZoomOut = () => {
    if (!svgRef.current) return
    d3.select(svgRef.current).transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      0.75
    )
  }

  const handleReset = () => {
    if (!svgRef.current || !containerRef.current) return
    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight
    
    d3.select(svgRef.current).transition().call(
      d3.zoom<SVGSVGElement, unknown>().transform as any,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
    )
  }

  return (
    <div className="h-full flex gap-4">
      {/* Graph container */}
      <div className="flex-1 relative" ref={containerRef}>
        <svg ref={svgRef} className="w-full h-full bg-muted/30 rounded-lg" />
        
        {/* Controls */}
        <div className="absolute top-4 left-4 flex flex-col gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 w-64 bg-background"
            />
          </div>
        </div>
        
        <div className="absolute bottom-4 right-4 flex gap-2">
          <Button variant="secondary" size="icon" onClick={handleZoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="secondary" size="icon" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="secondary" size="icon" onClick={handleReset}>
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Details panel */}
      {selectedNode && (
        <Card className="w-80 flex-shrink-0">
          <CardHeader>
            <CardTitle className="text-lg">{selectedNode.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Type</p>
                <p className="text-sm">{selectedNode.type}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">ID</p>
                <p className="text-sm font-mono">{selectedNode.id}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
