// app/settings.tsx - Part of the PrepSense mobile app
import { View, Text, StyleSheet, Switch, Pressable, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Stack } from 'expo-router';
import { CustomHeader } from './components/CustomHeader';
import { Ionicons } from '@expo/vector-icons';

type MenuItem = {
  title: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  onPress?: () => void;
  showChevron?: boolean;
  isToggle?: boolean;
  value?: boolean;
  onValueChange?: (value: boolean) => void;
} & (
  | { isToggle: true; onPress?: never; onValueChange: (value: boolean) => void; }
  | { isToggle?: false; onPress: () => void; onValueChange?: never; }
);

export default function SettingsScreen() {
  const router = useRouter();

  const menuItems: MenuItem[] = [
    {
      title: 'My Profile',
      icon: 'person-outline',
      onPress: () => router.push('/(tabs)/profile'),
      showChevron: true,
    },
    {
      title: 'Account',
      icon: 'person-circle-outline',
      onPress: () => console.log('Navigate to Account'),
      showChevron: true,
    },
    {
      title: 'Notifications',
      icon: 'notifications-outline',
      onPress: () => console.log('Navigate to Notifications'),
      showChevron: true,
    },
    {
      title: 'Dark Mode',
      icon: 'moon-outline',
      isToggle: true,
      value: false,
      onValueChange: (value) => console.log('Dark mode:', value),
    },
    {
      title: 'Help & Support',
      icon: 'help-circle-outline',
      onPress: () => console.log('Navigate to Help & Support'),
      showChevron: true,
    },
    {
      title: 'About',
      icon: 'information-circle-outline',
      onPress: () => console.log('Navigate to About'),
      showChevron: true,
    },
    {
      title: 'Sign Out',
      icon: 'log-out-outline',
      onPress: () => {
        // Handle sign out
        console.log('User signed out');
        router.replace('/(auth)/sign-in');
      },
    },
  ];

  return (
    <View style={styles.container}>
      <Stack.Screen
        options={{
          headerShown: true,
          header: () => (
            <CustomHeader 
              title="Settings" 
              showBackButton={true} 
            />
          ),
        }}
      />
      <ScrollView style={styles.scrollView}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>
          {menuItems.slice(0, 2).map((item, index) => (
            <MenuItem key={index} {...item} />
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          {menuItems.slice(2, 4).map((item, index) => (
            <MenuItem key={index + 2} {...item} />
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Support</Text>
          {menuItems.slice(4, 6).map((item, index) => (
            <MenuItem key={index + 4} {...item} />
          ))}
        </View>

        <View style={styles.section}>
          {menuItems.length > 6 && <MenuItem {...menuItems[6]} />}
        </View>
      </ScrollView>
    </View>
  );
}

function MenuItem({
  title,
  icon,
  onPress,
  showChevron = false,
  isToggle = false,
  value = false,
  onValueChange = () => {},
}: MenuItem) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.menuItem,
        pressed && { backgroundColor: 'rgba(0,0,0,0.05)' },
      ]}
      onPress={onPress}
      disabled={isToggle}
    >
      <View style={styles.menuItemLeft}>
        <Ionicons name={icon} size={24} color="#297A56" style={styles.icon} />
        <Text style={styles.menuItemText}>{title}</Text>
      </View>
      
      {isToggle ? (
        <Switch
          value={value}
          onValueChange={onValueChange}
          trackColor={{ false: '#767577', true: '#81c784' }}
          thumbColor={value ? '#297A56' : '#f4f3f4'}
        />
      ) : showChevron ? (
        <Ionicons name="chevron-forward" size={20} color="#ccc" />
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    backgroundColor: '#fff',
    marginBottom: 16,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#eee',
  },
  sectionTitle: {
    padding: 16,
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderColor: '#f0f0f0',
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  icon: {
    marginRight: 16,
    width: 24,
  },
  menuItemText: {
    fontSize: 16,
    color: '#333',
  },
});
