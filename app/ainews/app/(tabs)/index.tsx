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

// Update this with your backend's URL
const BACKEND_URL = "http://AINewsBackend.eu.pythonanywhere.com";

const InfiniteScrollPage = () => {
  const [data, setData] = useState([]);        // Array of news articles
  const [loading, setLoading] = useState(false); // Loading indicator
  const [hasMore, setHasMore] = useState(true);  // Flag for more data (if paginated)

  // Fetch news data from the backend /top-news endpoint
  const fetchData = async () => {
    if (loading || !hasMore) {
      console.log('Skipping fetch: loading=', loading, ', hasMore=', hasMore);
      return;
    }
    console.log('Starting data fetch...');
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/top-news`);
      console.log('Fetch response received:', response);
      const json = await response.json();
      console.log('Parsed JSON:', json);
      // Expecting the backend to return an object like { articles: [...] }
      if (json.articles && json.articles.length > 0) {
        console.log('Articles found, updating state with articles:', json.articles);
        setData(json.articles);
        // If backend only returns one batch of news, disable further fetching.
        setHasMore(false);
      } else {
        console.log('No articles found, setting hasMore to false');
        setHasMore(false);
      }
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      console.log('Fetch complete, setting loading to false');
      setLoading(false);
    }
  };

  // Initial fetch on mount
  useEffect(() => {
    console.log('Component mounted, initiating first data fetch...');
    fetchData();
  }, []);

  // Render each news article card
  const renderItem = ({ item, index }) => {
    console.log(`Rendering item at index ${index}:`, item);
    return (
      <View style={styles.mediaCard}>
        <Image
          source={require('../../assets/images/react-logo.png')}
          style={styles.backgroundImage}
        />
        <View style={styles.overlay}>
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.newsBody}>
            {item.summary ? item.summary : item.content}
          </Text>
        </View>
      </View>
    );
  };

  // Render footer while loading new data
  const renderFooter = () => {
    if (!loading) return null;
    console.log('Rendering footer loader...');
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
      keyExtractor={(item, index) => String(index)}
      pagingEnabled                  // Enables full-screen paging
      decelerationRate="fast"        // Helps snapping effect
      showsVerticalScrollIndicator={false}
      onEndReached={() => {
        console.log('End of list reached, fetching more data...');
        fetchData();
      }}
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
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingVertical: 30,
    // Semi-transparent overlay for readability over the image
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    // Rounded corners on the top for a modern look
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
    textShadowColor: 'rgba(0, 0, 0, 0.75)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  newsBody: {
    color: '#ddd',
    fontSize: 18,
    lineHeight: 26,
    textShadowColor: 'rgba(0, 0, 0, 0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  loader: {
    paddingVertical: 20,
    alignSelf: 'center',
  },
});

export default InfiniteScrollPage;
