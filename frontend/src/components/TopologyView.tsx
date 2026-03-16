import React, { useState, useEffect, useCallback } from 'react'
import ReactFlow, { 
  addEdge, 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge
} from 'react-flow-renderer'
import { Box, Heading, Spinner, Center, useColorModeValue } from '@chakra-ui/react'
import axios from 'axios'

const API_BASE = '/api/v1'

export const TopologyView = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)

  const bgColor = useColorModeValue('gray.50', 'gray.800')

  const fetchTopology = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/topology`)
      const { nodes: newNodes, edges: newEdges } = response.data
      
      // Simple layout logic: assign random positions if not present
      const positionedNodes = newNodes.map((node: Node, index: number) => ({
        ...node,
        position: node.position || { x: Math.random() * 400, y: index * 100 },
        style: {
          background: node.data.kind === 'node' ? '#2b6cb0' : 
                     node.data.kind === 'pod' ? '#38a169' : 
                     node.data.kind === 'service' ? '#d69e2e' : '#718096',
          color: 'white',
          borderRadius: '8px',
          padding: '10px',
          width: 150,
          textAlign: 'center' as const
        }
      }))

      setNodes(positionedNodes)
      setEdges(newEdges)
    } catch (error) {
      console.error("Failed to fetch topology", error)
    } finally {
      setLoading(false)
    }
  }, [setNodes, setEdges])

  useEffect(() => {
    fetchTopology()
    const interval = setInterval(fetchTopology, 30000)
    return () => clearInterval(interval)
  }, [fetchTopology])

  if (loading) {
    return (
      <Center h="500px">
        <Spinner size="xl" />
      </Center>
    )
  }

  return (
    <Box h="700px" w="full" bg={bgColor} borderRadius="xl" border="1px" borderColor="gray.200">
      <Heading size="md" p="4">Resource Topology Map</Heading>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </Box>
  )
}
