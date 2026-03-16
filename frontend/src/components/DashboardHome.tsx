import React from 'react'
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Heading,
  Text,
  Card,
  CardBody,
  Stack,
  Divider,
  Icon,
  Flex
} from '@chakra-ui/react'
import { FiCpu, FiServer, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi'

export const DashboardHome = () => {
  return (
    <Box>
      <Heading size="lg" mb="6">Cluster Overview</Heading>
      
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing="6" mb="8">
        <StatCard 
          label="Nodes" 
          value="3" 
          helpText="All Ready" 
          icon={FiServer} 
          color="blue.500"
        />
        <StatCard 
          label="Pods" 
          value="42" 
          helpText="89% Healthy" 
          icon={FiCpu} 
          color="purple.500"
          arrow="decrease"
        />
        <StatCard 
          label="Active Alerts" 
          value="2" 
          helpText="Requires Action" 
          icon={FiAlertTriangle} 
          color="orange.500"
        />
        <StatCard 
          label="Agent Status" 
          value="Active" 
          helpText="Collecting Telemetry" 
          icon={FiCheckCircle} 
          color="green.500"
        />
      </SimpleGrid>

      <Heading size="md" mb="4">Quick Insights</Heading>
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing="6">
        <Card variant="outline">
          <CardBody>
            <Heading size="xs" textTransform="uppercase" mb="2">Latest AI Analysis</Heading>
            <Text fontSize="sm">
              Traced <b>CrashLoopBackOff</b> in <code>payment-api</code> to <b>OOMKilled</b>. 
              Suggested fix: Increase memory limits by 256Mi.
            </Text>
          </CardBody>
        </Card>
        <Card variant="outline">
          <CardBody>
            <Heading size="xs" textTransform="uppercase" mb="2">Cluster Topology</Heading>
            <Text fontSize="sm">
              Detected 15 new relationships in the last 10 minutes.
              Traefik Ingress is currently routing traffic to 8 services.
            </Text>
          </CardBody>
        </Card>
      </SimpleGrid>
    </Box>
  )
}

const StatCard = ({ label, value, helpText, icon, color, arrow }: any) => {
  return (
    <Card variant="elevated">
      <CardBody>
        <Flex justifyContent="space-between" alignItems="center">
          <Box>
            <Stat>
              <StatLabel color="gray.500">{label}</StatLabel>
              <StatNumber fontSize="3xl">{value}</StatNumber>
              <StatHelpText>
                {arrow && <StatArrow type={arrow} />}
                {helpText}
              </StatHelpText>
            </Stat>
          </Box>
          <Icon as={icon} boxSize="10" color={color} opacity="0.8" />
        </Flex>
      </CardBody>
    </Card>
  )
}
