// Heart Mapping App (React Native + Expo, international-ready)
import React from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ImageBackground,
  StatusBar,
} from 'react-native';

const sampleQuiz = [
  { question: 'I often feel a strong emotional connection with people around me.', heart: 'C' },
  { question: 'I feel driven to take meaningful action in the world.', heart: 'D' },
  { question: 'I analyze the causes of suffering — mine and others’.', heart: 'G' },
  { question: 'I often make decisions based on intuition more than logic.', heart: 'I' },
  { question: 'I believe there is a deeper meaning behind everything.', heart: 'E' },
];

class App extends React.Component {
  state = {
    started: false,
    currentQuestion: 0,
    answers: [],
  };

  handleStart = () => {
    this.setState({ started: true });
  };

  handleAnswer = (value) => {
    const { currentQuestion, answers } = this.state;
    const updatedAnswers = [...answers, value];

    if (currentQuestion + 1 < sampleQuiz.length) {
      this.setState({
        currentQuestion: currentQuestion + 1,
        answers: updatedAnswers,
      });
    } else {
      // You can later handle result calculation here
      alert('Quiz complete!');
      this.setState({ started: false, currentQuestion: 0, answers: [] });
    }
  }

  render() {

    const { started } = this.state;
    return (
      <ImageBackground
        source={{ uri: 'https://upload.wikimedia.org/wikipedia/commons/7/75/Gray_Granite_Texture.jpg' }}
        style={styles.container}
        resizeMode="cover"
      >
        <StatusBar barStyle="light-content" />
        {!started ? (
          <View style={styles.centerBox}>
            <Text style={styles.title}>🔮 Discover Your Heart</Text>
            <TouchableOpacity style={styles.button} onPress={this.handleStart}>
              <Text style={styles.buttonText}>Start Quiz</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.centerBox}>
            <Text style={styles.title}>Question {this.state.currentQuestion + 1} of {sampleQuiz.length}</Text>
            <Text style={styles.question}>{sampleQuiz[this.state.currentQuestion].question}</Text>
            <View style={{ marginTop: 24 }}>
              {[1, 2, 3, 4, 5].map((value) => (
                <TouchableOpacity
                  key={value}
                  style={[styles.button, { marginVertical: 4 }]}
                  onPress={() => this.handleAnswer(value)}
                >
                  <Text style={styles.buttonText}>{value}</Text>
                </TouchableOpacity>
              ))}
            </View>

          </View>
        )}
      </ImageBackground>
    );
  }

}
export default App;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  centerBox: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    padding: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 24,
  },
  button: {
    backgroundColor: '#000',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 4,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  question: {
    fontSize: 22,
    color: '#fff',
    textAlign: 'center',
  },
});
