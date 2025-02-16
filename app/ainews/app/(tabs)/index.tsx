import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Dimensions,
  Image,
} from 'react-native';

const { width, height } = Dimensions.get('window');

// Create a mock dataset with 50 items (each representing a video)
const TOTAL_ITEMS = 50;
const PAGE_SIZE = 5;
const MOCK_DATA = Array.from({ length: TOTAL_ITEMS }, (_, index) => ({
  id: index + 1,
  title: `News ${index + 1}`,
  // Using the local image asset for thumbnail
  thumbnail: require('../../assets/images/react-logo.png'),
}));

// Simulate an API call that returns a paginated list of items
const simulateFetch = (page) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const start = (page - 1) * PAGE_SIZE;
      const end = start + PAGE_SIZE;
      const result = MOCK_DATA.slice(start, end);
      resolve(result);
    }, 1000); // Simulate network delay of 1 second
  });
};

const InfiniteScrollPage = () => {
  const [data, setData] = useState([]);      // Array of items
  const [page, setPage] = useState(1);         // Current page number for pagination
  const [loading, setLoading] = useState(false); // Loading indicator
  const [hasMore, setHasMore] = useState(true);  // Flag to indicate if more data is available

  // Function to fetch data from your simulated API
  const fetchData = async () => {
    if (loading || !hasMore) return;
    setLoading(true);
  
    try {
      const result = await simulateFetch(page);
  
      if (result.length === 0) {
        setHasMore(false); // No more data to load
      } else {
        setData(prevData => [...prevData, ...result]);
        setPage(prevPage => prevPage + 1);
      }
    } catch (error) {
      console.error('Error fetching data: ', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, []);

  // Render each full-screen video item
  const renderItem = ({ item }) => (
    <View style={styles.mediaCard}>
      {/* Thumbnail or Video component can go here */}
      <Image source={item.thumbnail} style={styles.backgroundImage} />

      {/* Overlay for video details (like title, user info, icons) */}
      <View style={styles.overlay}>
        <Text style={styles.title}>{item.title}</Text>
        <Text style={styles.newsBody}>
          This is a sample news body for {item.title}. It can be multiple lines long.
          For demonstration purposes, we are limiting the text to a few lines.
          Here is another line to make it longer.
        </Text>
        <Text style={styles.caption}>This is a sample caption for {item.title}.</Text>
        {/* Add more overlay icons or buttons as needed */}
      </View>
    </View>
  );

  // Render footer component while new data is loading
  const renderFooter = () => {
    if (!loading) return null;
    return (
      <View style={styles.loader}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  };

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={(item) => String(item.id)}
      pagingEnabled                  // Enables full-screen paging
      decelerationRate="fast"        // Helps snapping effect
      showsVerticalScrollIndicator={false}
      onEndReached={fetchData}        // Trigger fetch when reaching end
      onEndReachedThreshold={0.5}
      ListFooterComponent={renderFooter}
    />
  );
};

const styles = StyleSheet.create({
  mediaCard: {
    width,
    height,
    backgroundColor: '#000',
    position: 'relative',
  },
  backgroundImage: {
    width,
    height,
    resizeMode: 'cover',
  },
  overlay: {
    position: 'absolute',
    bottom: 50,
    left: 20,
    right: 20,
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  newsBody: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  caption: {
    color: '#fff',
    fontSize: 14,
  },
  loader: {
    position: 'absolute',
    bottom: 20,
    alignSelf: 'center',
  },
});

export default InfiniteScrollPage;
