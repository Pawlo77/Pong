from kivy.app import App
  
# The ScrollView widget provides a scrollable view 
from kivy.uix.recycleview import RecycleView
from kivy.lang import Builder


Builder.load_string("""
<ExampleViewer>:
    viewclass: 'Button'  # defines the viewtype for the data items.
    orientation: "vertical"
    spacing: 40
    padding:10, 10
    space_x: self.size[0]/3
  
    RecycleBoxLayout:
        color:(0, 0.7, 0.4, 0.8)
        default_size: None, dp(56)
  
        # defines the size of the widget in reference to width and height
        default_size_hint: 0.4, None 
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical' # defines
""")
  
  
# Define the Recycleview class which is created in .kv file
class ExampleViewer(RecycleView):
    def __init__(self, **kwargs):
        super(ExampleViewer, self).__init__(**kwargs)
        self.data = [{'text': str(x)} for x in range(20)]
  
# Create the App class with name of your app.
class SampleApp(App):
    def build(self):
        return ExampleViewer()
  
# run the App
SampleApp().run()