import React, { useState, useEffect } from 'react'
import {
  Box,
  Flex,
  Text,
  IconButton,
  Button,
  Stack,
  useColorMode,
  useColorModeValue,
  Drawer,
  DrawerContent,
  useDisclosure,
  Icon,
  Link,
  HStack,
  Heading,
  Badge,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useToast
} from '@chakra-ui/react'
import {
  FiHome,
  FiActivity,
  FiSettings,
  FiMenu,
  FiSun,
  FiMoon,
  FiCpu,
  FiDatabase,
  FiZap
} from 'react-icons/fi'
import { TopologyView } from './components/TopologyView'
import { IncidentFeed } from './components/IncidentFeed'
import { SettingsPanel } from './components/SettingsPanel'
import { DashboardHome } from './components/DashboardHome'

const LinkItems = [
  { name: 'Dashboard', icon: FiHome, view: 'dashboard' },
  { name: 'Topology', icon: FiZap, view: 'topology' },
  { name: 'Incidents', icon: FiActivity, view: 'incidents' },
  { name: 'Settings', icon: FiSettings, view: 'settings' },
]

export default function App() {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [activeView, setActiveView] = useState('dashboard')
  const { colorMode, toggleColorMode, setColorMode } = useColorMode()
  const toast = useToast()

  // Custom theme handling for Solarized
  const [themeMode, setThemeMode] = useState('dark') // dark, white, solarized

  const handleThemeChange = (mode: string) => {
    setThemeMode(mode)
    if (mode === 'dark') setColorMode('dark')
    if (mode === 'white') setColorMode('light')
    if (mode === 'solarized') {
      setColorMode('dark')
      // Additional solarized styling handled by useColorModeValue or custom css
    }
  }

  const bg = useColorModeValue(
    themeMode === 'solarized' ? 'solarized.base3' : 'white',
    themeMode === 'solarized' ? 'solarized.base03' : 'gray.900'
  )
  const color = useColorModeValue(
    themeMode === 'solarized' ? 'solarized.base01' : 'gray.800',
    themeMode === 'solarized' ? 'solarized.base0' : 'white'
  )

  return (
    <Box minH="100vh" bg={bg} color={color}>
      <SidebarContent
        onClose={() => onClose}
        display={{ base: 'none', md: 'block' }}
        activeView={activeView}
        setActiveView={setActiveView}
        themeMode={themeMode}
      />
      <Drawer
        autoFocus={false}
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        returnFocusOnClose={false}
        onOverlayClick={onClose}
        size="full">
        <DrawerContent>
          <SidebarContent onClose={onClose} activeView={activeView} setActiveView={setActiveView} themeMode={themeMode} />
        </DrawerContent>
      </Drawer>
      {/* mobilenav */}
      <MobileNav onOpen={onOpen} handleThemeChange={handleThemeChange} themeMode={themeMode} />
      <Box ml={{ base: 0, md: 60 }} p="4">
        {activeView === 'dashboard' && <DashboardHome />}
        {activeView === 'topology' && <TopologyView />}
        {activeView === 'incidents' && <IncidentFeed />}
        {activeView === 'settings' && <SettingsPanel />}
      </Box>
    </Box>
  )
}

interface SidebarProps {
  onClose: () => void
  activeView: string
  setActiveView: (view: string) => void
  themeMode: string
  [key: string]: any
}

const SidebarContent = ({ onClose, activeView, setActiveView, themeMode, ...rest }: SidebarProps) => {
  const bg = useColorModeValue(
    themeMode === 'solarized' ? 'solarized.base2' : 'white',
    themeMode === 'solarized' ? 'solarized.base02' : 'gray.800'
  )
  const borderColor = useColorModeValue(
    themeMode === 'solarized' ? 'solarized.base1' : 'gray.200',
    themeMode === 'solarized' ? 'solarized.base01' : 'gray.700'
  )

  return (
    <Box
      transition="3s ease"
      bg={bg}
      borderRight="1px"
      borderRightColor={borderColor}
      w={{ base: 'full', md: 60 }}
      pos="fixed"
      h="full"
      {...rest}>
      <Flex h="20" alignItems="center" mx="8" justifyContent="space-between">
        <Heading size="md" color="blue.400">K3s-Sentinel</Heading>
      </Flex>
      {LinkItems.map((link) => (
        <NavItem
          key={link.name}
          icon={link.icon}
          active={activeView === link.view}
          onClick={() => {
            setActiveView(link.view)
            onClose()
          }}
          themeMode={themeMode}
        >
          {link.name}
        </NavItem>
      ))}
    </Box>
  )
}

interface NavItemProps {
  icon: any
  children: string
  active?: boolean
  onClick: () => void
  themeMode: string
}
const NavItem = ({ icon, children, active, onClick, themeMode, ...rest }: NavItemProps) => {
  const activeBg = useColorModeValue(
    themeMode === 'solarized' ? 'solarized.blue' : 'blue.500',
    themeMode === 'solarized' ? 'solarized.blue' : 'blue.600'
  )
  const activeColor = 'white'
  const hoverBg = useColorModeValue('blue.50', 'blue.900')

  return (
    <Link href="#" style={{ textDecoration: 'none' }} _focus={{ boxShadow: 'none' }} onClick={onClick}>
      <Flex
        align="center"
        p="4"
        mx="4"
        borderRadius="lg"
        role="group"
        cursor="pointer"
        bg={active ? activeBg : 'transparent'}
        color={active ? activeColor : 'inherit'}
        _hover={{
          bg: active ? activeBg : hoverBg,
        }}
        {...rest}>
        {icon && (
          <Icon
            mr="4"
            fontSize="16"
            as={icon}
          />
        )}
        {children}
      </Flex>
    </Link>
  )
}

interface MobileProps {
  onOpen: () => void
  handleThemeChange: (mode: string) => void
  themeMode: string
}
const MobileNav = ({ onOpen, handleThemeChange, themeMode, ...rest }: MobileProps) => {
  const bg = useColorModeValue(
    themeMode === 'solarized' ? 'solarized.base2' : 'white',
    themeMode === 'solarized' ? 'solarized.base02' : 'gray.800'
  )
  const borderColor = useColorModeValue(
    themeMode === 'solarized' ? 'solarized.base1' : 'gray.200',
    themeMode === 'solarized' ? 'solarized.base01' : 'gray.700'
  )

  return (
    <Flex
      ml={{ base: 0, md: 60 }}
      px={{ base: 4, md: 4 }}
      height="20"
      alignItems="center"
      bg={bg}
      borderBottomWidth="1px"
      borderBottomColor={borderColor}
      justifyContent={{ base: 'space-between', md: 'flex-end' }}
      {...rest}>
      <IconButton
        display={{ base: 'flex', md: 'none' }}
        onClick={onOpen}
        variant="outline"
        aria-label="open menu"
        icon={<FiMenu />}
      />

      <Heading
        display={{ base: 'flex', md: 'none' }}
        size="md"
        color="blue.400">
        K3s-Sentinel
      </Heading>

      <HStack spacing={{ base: '0', md: '6' }}>
        <Menu>
          <MenuButton as={Button} variant="ghost" rightIcon={<FiSun />}>
            Theme
          </MenuButton>
          <MenuList>
            <MenuItem onClick={() => handleThemeChange('white')}>White Mode</MenuItem>
            <MenuItem onClick={() => handleThemeChange('dark')}>Dark Mode</MenuItem>
            <MenuItem onClick={() => handleThemeChange('solarized')}>Solarized Mode</MenuItem>
          </MenuList>
        </Menu>
        <Flex alignItems={'center'}>
           <Badge colorScheme="green">Connected</Badge>
        </Flex>
      </HStack>
    </Flex>
  )
}
