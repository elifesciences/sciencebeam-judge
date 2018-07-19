def mean(data):
  return sum(data) / len(data)

def safe_mean(data, default_value=0):
  return mean(data) if data else default_value
