describe("ie global tests", function() {

  var element;
  beforeEach(function () {
    element = document.createElement("div")
  })

  it("NamedNodeMap should be global", function () {
    expect("NamedNodeMap" in window).toBe(true)
  })

  it("an element's attributes collection should be an instance of NamedNodeMap", function () {
    expect(element.attributes instanceof NamedNodeMap).toBe(true)
  })
  it ("a new element's attributes length should be zero", function () {
    expect(element.attributes.length === 0).toBe(true);
    expect(element.hasAttributes() === false).toBe(true);
  })
  it ("adding an attribute updates the element, the attribute and its attributes collection correctly", function () {
      var data = "s12312"
      element.setAttribute("data-test",data);
      expect(element.hasAttributes() === true).toBe(true, "hasAttributes hsould be true")
      expect(element.hasAttribute("data-test") === true).toBe(true, "hasAttribute should pick up the attribute")
      expect(element.attributes.length == 1).toBe(true, "length is not 1")
      expect(element.attributes["data-test"].nodeValue == data).toBe(true, "nodeValue is not correct")
      expect(element.attributes[0] == element.attributes["data-test"]).toBe(true, "attributes index/names are not correct")
      expect(element.attributes.item(0) == element.attributes[0]).toBe(true, "item() not returning correct value")
      expect(element.getAttribute("data-test") == data).toBe(true, "getAttribute should return the correct value");
      expect(element.attributes[0].ownerElement == element).toBe(true, "ownerElement property should be set correctly")
      expect(element.attributes.item(0).isId === false).toBe(true, "isId should be set correctly")
      expect(element.attributes[0].nodeType === 2).toBe(true, "nodeType is correct")
  })
it("adding existing attributes should behave correctly", function () {
    element.setAttribute("data-test","test")
    element.setAttribute("data-test","again")
    expect(element.attributes.length === 1).toBe(true,"adding same attribute with different values should not increase length")
    expect(element.attributes[0].nodeValue === "again").toBe(true, "nodeValue is updated correctly")

})
  it("adding an id attribute should change all appropriate properties", function () {
      var id = "foo"
      element.setAttribute("id",id);
      expect(element.hasAttribute("id") === true).toBe(true, "id attribute should be detected")
      expect(element.id === id).toBe(true, "id property of element should be set correctly")
      expect(element.attributes.id.isId === true).toBe(true, "id attribute should be marked as true")
      element.removeAttribute("id")
      expect(element.id === id).toBe(false,"removing the attribute should remove the id property")
      element.id = id;
      expect(element.hasAttribute("id") === true).toBe(true,"setting the id property should create an attribute")
  })
  it("adding a style attribute should change all appropriate properties", function () {
      var style = "color:red"
      element.setAttribute("style",style);
      expect(element.hasAttribute("style") === true).toBe(true, "style attribute should be detected");
      expect(element.style.color === "red").toBe(true, "style property updated correctly");
      expect(element.getAttribute("style") === style).toBe(true);
      expect(element.getAttributeNode("style").nodeValue === style).toBe(true);
      //bit cheeky but we know that IE capitalizes...
      expect(/color\:\s*red\s*;?/.test(element.style.cssText)).toBe(true)
      element.removeAttribute("style")
      expect(element.attributes.length === 0 ).toBe(true)
      expect(element.style.color === "red").toBe(false)
      expect(element.style.cssText === "").toBe(true)
  })
  it("adding a class attribute should change all appropriate properties", function () {
      var classNames = "foo bar"
      element.setAttribute("class",classNames);
      expect(element.hasAttribute("class") === true).toBe(true, "class attribute should be detected");
      expect(element.className === classNames).toBe(true, "className property updated correctly");
      expect(element.getAttribute("class") === classNames).toBe(true);
      expect(element.getAttributeNode("class").nodeValue === classNames).toBe(true);
      element.removeAttribute("class")
      expect(element.attributes.length === 0 ).toBe(true)
      expect(element.className === "").toBe(true)
  })



});